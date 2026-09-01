import os 
from app import config
from fastapi import HTTPException
from app.graph.registry import get_graph
from fastapi import FastAPI
from app.github.sync import clone_repo
from pydantic import BaseModel
from app.parser.pipeline import process_repo
from app.graph.registry import store_graph
from app.graph.vector_store import search
from app.rag.engine import answer_question

class RepoUrl(BaseModel):
    repo_url: str
class Query(BaseModel):
    question: str

app = FastAPI(title="RepoGraph", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Hello World", "status": "running", "app": "RepoGraph"}
@app.post("/repos/clone")
def clone_repo_endpoint(repo: RepoUrl):
    full_path, owner, repo_name = clone_repo(repo.repo_url)
    graph = process_repo(owner, repo_name)
    store_graph(owner, repo_name, graph)    
    return {
        "message": "Repo cloned successfully", 
        "full_path": full_path, 
        "owner": owner, 
        "repo_name": repo_name,
        "graph": {
            "nodes": graph.G.number_of_nodes(),
            "edges": graph.G.number_of_edges()
        }
    }
@app.get("/repos/{owner}/{repo_name}/query")
async def query_endpoint(owner: str, repo_name: str, function_name: str):
    graph = get_graph(owner, repo_name)
    if not graph:
        raise HTTPException(status_code=404, detail="Repo not found")
    if graph.G.has_node(function_name):
        return {
                "function": function_name,
                "callers": graph.get_callers(function_name),
                "callees": graph.get_callees(function_name)
            }
    else:
        raise HTTPException(status_code=404, detail="Function not found")
    
@app.post("/repos/{owner}/{repo_name}/index")
def index_repo_endpoint(owner: str, repo_name: str):
    path = os.path.join(config.REPOS_DIR,owner,repo_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Repo not found")
    graph = process_repo(owner, repo_name)
    store_graph(owner, repo_name, graph)
    return {
        "message": "Repo indexed successfully",
        "owner": owner,
        "repo_name": repo_name,
        "graph": {
            "nodes": graph.G.number_of_nodes(),
            "edges": graph.G.number_of_edges()
        }
    }

@app.get("/repos/{owner}/{repo_name}/search")
def search_endpoint(owner: str, repo_name: str, query: str):
    results = search(owner, repo_name, query)
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    return results
    
@app.post("/repos/{owner}/{repo_name}/ask")
def ask_endpoint(owner: str, repo_name: str, query: Query):
    results = answer_question(owner, repo_name, query.question)
    if not results:
        raise HTTPException(status_code=404, detail="Could not answer question")
    return {"answer": results}

@app.get("/repos/{owner}/{repo_name}/debug")
def debug_endpoint(owner: str, repo_name: str, question: str = ""):
    from app.rag.engine import resolve_seed_node
    graph = get_graph(owner, repo_name)
    if not graph:
        return {"error": "Graph not loaded. Re-index first."}
    
    call_edges = [(u, v) for u, v, d in graph.G.edges(data=True) if d.get('type') == 'calls']
    sample_edges = [
        {"from": graph.G.nodes[u].get('name', u), "to": graph.G.nodes[v].get('name', v)}
        for u, v in call_edges[:20]
    ]
    
    result = {
        "nodes": graph.G.number_of_nodes(),
        "edges": graph.G.number_of_edges(),
        "call_edges": len(call_edges),
        "sample_call_edges": sample_edges,
        "name_index_size": len(graph.name_index),
        "sample_names": list(graph.name_index.keys())[:20],
    }
    
    if question:
        vector_res = search(owner, repo_name, question, n_results=5)
        seed = resolve_seed_node(graph, question, vector_res)
        seed_name = graph.G.nodes[seed].get('name') if seed else None
        bfs_result = graph.bfs(seed, max_depth=4, max_nodes=15) if seed else []
        bfs_names = [graph.G.nodes[n].get('name', n) for n in bfs_result] if bfs_result else []
        result["seed_node_id"] = seed
        result["seed_node_name"] = seed_name
        result["bfs_path"] = bfs_names
    
    return result
