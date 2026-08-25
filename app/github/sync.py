import os
from git import Repo
from app import config

def clone_repo(repo_url: str):
    repo_url = repo_url.rstrip("/")
    base_path = config.REPOS_DIR

    repo_name = repo_url.split("/")[-1].removesuffix(".git")
    owner = repo_url.split("/")[-2]
    full_path = os.path.join(base_path, owner, repo_name)

    if os.path.exists(full_path):
        raise Exception('Repo already exists')

    os.makedirs(full_path, exist_ok=True)
    Repo.clone_from(repo_url, full_path)
    return full_path, owner, repo_name
