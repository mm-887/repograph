REGISTRY = {}

def store_graph(owner, repo_name, graph):
    key = (owner, repo_name)
    REGISTRY[key] = graph

def get_graph(owner, repo_name):
    key = (owner, repo_name)
    return REGISTRY.get(key)

