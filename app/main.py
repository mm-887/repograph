from fastapi import HTTPException
from app.graph.registry import get_graph
from fastapi import FastAPI
from app.github.sync import clone_repo
from pydantic import BaseModel
from app.parser.pipeline import process_repo
from app.graph.registry import store_graph

class RepoUrl(BaseModel):
    repo_url: str

app = FastAPI(title="RepoGraph", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Hello World", "status": "running", "app": "RepoGraph"}
@app.post("/repos/clone")
async def clone_repo_endpoint(repo: RepoUrl):
    full_path, owner, repo_name = clone_repo(repo.repo_url)
    graph = process_repo(full_path)
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
    

    
