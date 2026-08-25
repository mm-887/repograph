from fastapi import FastAPI
from app.github.sync import clone_repo
from pydantic import BaseModel

class RepoUrl(BaseModel):
    repo_url: str

app = FastAPI(title="RepoGraph", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Hello World", "status": "running", "app": "RepoGraph"}
@app.post("/repos/clone")
async def clone_repo_endpoint(repo: RepoUrl):
    full_path, owner, repo_name = clone_repo(repo.repo_url)
    return {
        "message": "Repo cloned successfully", 
        "full_path": full_path, 
        "owner": owner, 
        "repo_name": repo_name
    }