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

class RepoUrl(BaseModel):
    repo_url: str

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
    
    
