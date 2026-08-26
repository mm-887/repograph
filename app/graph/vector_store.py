import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chromadb')
os.makedirs(CHROMA_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_PATH)

embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def chunk_text(text, chunk_size = 1000, overlap = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def index_entities(owner, repo_name, entities):
    collection_name = f"{owner}.{repo_name}"
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_func
    )
    existing_ids = collection.get("ids")["ids"]
    
    new_ids = []
    documents = []
    metadatas = []

    for entity in entities:
        if 'code' not in entity or not entity['code']:
            continue
        chunks = chunk_text(entity['code'])

        for i,chunk in enumerate(chunks):
            chunk_id = f"{entity['id']}_chunk_{i}"

            meta = {k:v for k,v in entity.items() if k != 'code'}

            new_ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(meta)
        
    if new_ids:
        collection.upsert(
            ids=new_ids,
            documents=documents,
            metadatas=metadatas
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

