from app.graph.vector_store import search
from app.graph.registry import get_graph
from app.llm.factory import get_llm_provider

def answer_question(owner:str, repo_name:str, question:str):
    vector_res = search(owner, repo_name, question, n_results=5)
    if not vector_res or not vector_res['documents'] or not vector_res['documents'][0]:
        return "No context found"
    graph = get_graph(owner, repo_name)
    code_snippets = []
    relationships = []
    for i in range(len(vector_res['documents'][0])):
        doc = vector_res['documents'][0][i]
        meta = vector_res['metadatas'][0][i]
        
        code_snippets.append(f"File: {meta['file']}\nCode:\n{doc}\n")
        
        node_name = meta.get('name')
        if graph and node_name and graph.G.has_node(node_name):
            callers = graph.get_callers(node_name)
            callees = graph.get_callees(node_name)
            if callers:
                relationships.append(f"Functions that call '{node_name}': {', '.join(callers)}")
            if callees:
                relationships.append(f"'{node_name}' calls these functions: {', '.join(callees)}")

    system_prompt="""
You are RepoGraph, an AI assistant for understanding software repositories.

Your task is to answer questions about the repository using ONLY the repository
context provided to you in the prompt.

The context may contain source-code snippets, file paths, symbols, and structural
relationships extracted from the repository's knowledge graph and semantic
retrieval system.

Rules:

1. Treat the provided repository context as the authoritative source for
   repository-specific claims.

2. Do not invent files, functions, classes, variables, relationships, behavior,
   or implementation details that are not supported by the provided context.

3. You may use your general programming knowledge to explain what the provided
   code is doing, but clearly distinguish general explanations from facts about
   this repository.

4. When the retrieved context is insufficient to answer the question reliably,
   say so explicitly. Do not fill missing repository information with guesses.

5. When possible, identify the relevant file, class, function, or module in your
   answer so that the developer can locate the information in the repository.

6. When relationships such as CALLS, IMPORTS, DEFINES, CONTAINS, or INHERITS are
   provided, use them to explain how the relevant parts of the codebase are
   connected.

7. Prefer precise technical explanations over vague summaries.

8. Do not modify code or propose that code exists when it is not present in the
   supplied repository context.

9. If multiple pieces of context appear relevant but provide conflicting
   information, explicitly mention the conflict rather than silently choosing
   one.

10. Structure your answer appropriately for the question. For a simple lookup,
    answer directly. For an architectural question, explain the relevant
    components and their relationships."""
    user_prompt=f"""User Question: {question}
    
    <code_snippets>
    {chr(10).join(code_snippets)} 
    </code_snippets>
    
    <graph_relationships>
    {chr(10).join(relationships)}
    </graph_relationships>
    """
    provider = get_llm_provider()
    return provider.generate_response(system_prompt, user_prompt)