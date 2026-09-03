import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp.server.mcpserver import MCPServer
from app.graph.vector_store import search
from app.graph.registry import get_graph
from app.rag.engine import answer_question

mcp = MCPServer("RepoGraph")

@mcp.tool()
def repo_search_symbols(owner:str, repo_name:str, query:str, limit:int = 5) -> dict:
    """
    Search for classes, methods, and functions in the repository using semantic search.
    """
    return search(owner, repo_name, query, n_results=limit)


@mcp.tool()
def repo_trace_call_flow(owner:str, repo_name:str, symbol:str) -> dict:
    """
    Get the call flow of a function in the repository.
    """
    graph = get_graph(owner, repo_name)
    if not graph:
        return {"error": "Graph not found"}
    node_id = graph.resolve_node(symbol)
    if not node_id:
        return {"error": "Function not found"}
    path = graph.bfs(node_id, max_depth = 3, max_nodes=20, direction="out")
    nodes = [graph.G.nodes[nid].get('name', nid) for nid in path if nid != node_id] if path else []
    return {"seed": symbol, "call_flow":nodes}
    
@mcp.tool()
def repo_find_callers_and_subclasses(owner:str, repo_name:str, symbol:str) -> dict:
    """
    Find the callers and subclasses of a function in the repository.
    """
    graph = get_graph(owner, repo_name)
    if not graph:
        return {"error": "Graph not found"}
    node_id = graph.resolve_node(symbol)
    if not node_id:
        return {"error": "Function not found"}
    path = graph.bfs(node_id, max_depth = 3, max_nodes=20, direction="in")
    nodes = [graph.G.nodes[nid].get('name', nid) for nid in path if nid != node_id] if path else []
    return {"seed": symbol, "callers_and_subclasses":nodes}

@mcp.tool()
def repo_ask(owner:str, repo_name:str, question:str) -> dict:
    """
     Answer complex architectural, behavioral, or implementation questions about a repository using Graph-RAG.
    This tool resolves entry-point symbols, traverses the code call-graph and class inheritance hierarchy,
    hydrates relevant AST snippets, and returns a verified explanation with structured file and line citations.
    """
    result =  answer_question(owner, repo_name, question)
    if isinstance(result,str):
        return {"answer": result}
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")