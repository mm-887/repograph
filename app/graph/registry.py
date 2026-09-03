from app import config
import os, pickle
REGISTRY = {}

def store_graph(owner, repo_name, graph):
    file_path = _get_graph_path(owner, repo_name)
    with open(file_path, "wb") as f:
        pickle.dump(graph, f)
    key = (owner, repo_name)
    REGISTRY[key] = graph

def get_graph(owner, repo_name):
    key = (owner, repo_name)
    if key in REGISTRY:
        return REGISTRY[key]
    file_path = _get_graph_path(owner, repo_name)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            loaded_graph = pickle.load(f)
            REGISTRY[key] = loaded_graph
            return loaded_graph
    return None

def _get_graph_path(owner: str, repo_name: str) -> str:
    return os.path.join(config.GRAPHS_DIR, f"{owner}_{repo_name}.pickle")
