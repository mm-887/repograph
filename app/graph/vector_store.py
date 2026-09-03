import os
import chromadb
from chromadb.utils import embedding_functions
from app import config

os.makedirs(config.CHROMA_DIR, exist_ok=True)
client = chromadb.PersistentClient(path=config.CHROMA_DIR)

embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def create_retrieval_text(entity:dict) -> str:
    entity_type = entity.get('type')
    name = entity.get('name', '')
    file_path = entity.get('file', '')
    code = entity.get('code', '')
    if entity_type == 'function_definition':
        return f"File: {file_path}\nFunction: {name}\n{code}"
    elif entity_type == 'class_definition':
        return f"File: {file_path}\nClass: {name}\n{code[:600]}"
    return ""  
    

def chunk_text(text, chunk_size = 1000, overlap = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def index_entities(owner, repo_name, entities, batch_size=5000):
    collection_name = f"{owner}.{repo_name}"
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func
    )
    existing_ids = collection.get()["ids"]
    
    new_ids = []
    documents = []
    metadatas = []

    for entity in entities:
        doc_text = create_retrieval_text(entity)
        if not doc_text.strip():
            continue
        if len(doc_text) > 2500:
            chunks = chunk_text(doc_text, chunk_size=2000, overlap=300)
            for i,chunk in enumerate(chunks):
                chunk_id = f"{entity['id']}_chunk_{i}"
                new_ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({k: v for k, v in entity.items() if k != 'code'})
        else:
            new_ids.append(entity['id'])
            documents.append(doc_text)
            metadatas.append({k: v for k, v in entity.items() if k != 'code'})
        
    for start in range(0, len(new_ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=new_ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end]
        )

    stale_ids = list(set(existing_ids) - set(new_ids))
    if stale_ids:
        collection.delete(ids=stale_ids)
        
def search(owner, repo_name, query, n_results=5):
    collection_name = f"{owner}.{repo_name}"
    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_func
        )
    except Exception:
        return None
        
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results
