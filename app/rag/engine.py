import re
import numpy as np
from app.graph.vector_store import search, embedding_func
from app.graph.registry import get_graph
from app.llm.factory import get_llm_provider

def select_nodes_for_full_code(graph, seed_node: str, traversed_nodes: list, question: str, max_full_code: int = 4) -> set:
    selected = {seed_node}
    other_nodes = [n for n in traversed_nodes if n != seed_node]
    if not other_nodes:
        return selected

    node_summaries = []
    eligible_nodes = []

    for n in other_nodes:
        data = graph.G.nodes.get(n, {})
        code = data.get('code', '')
        if code and data.get('type') in ('function_definition', 'class_definition'):
            node_summaries.append(f"{data.get('name')}: {code[:300]}")
            eligible_nodes.append(n)

    if not eligible_nodes:
        return selected

    q_emb = np.array(embedding_func([question])[0])
    node_embs = np.array(embedding_func(node_summaries))
    scores = np.dot(node_embs, q_emb)
    ranked_indices = np.argsort(scores)[::-1]

    for idx in ranked_indices[:max_full_code - 1]:
        selected.add(eligible_nodes[idx])

    return selected


def resolve_seed_node(graph, question: str, vector_res: dict) -> str | None:
    if not graph:
        return None
    if not vector_res or not vector_res.get('metadatas') or not vector_res['metadatas'][0]:
        return None
    
    candidate_scores = {}
    for rank, meta in enumerate(vector_res['metadatas'][0]):
        node_id = meta.get('id')
        if node_id and graph.G.has_node(node_id):
            candidate_scores[node_id] = {"lexical": 0.0, "semantic": 1.0 - (rank * 0.15)}
        elif meta.get('name') in graph.name_index:
            for nid in graph.name_index[meta['name']]:
                candidate_scores[nid] = {"lexical": 0.0, "semantic": 1.0 - (rank * 0.15)}
                
    tokens = re.findall(r'[A-Za-z0-9_.]+', question)
    for token in tokens:
        leaf = token.split('.')[-1]
        for name_to_check in (token, leaf):
            if name_to_check in graph.name_index:
                for node_id in graph.name_index[name_to_check]:
                    if node_id not in candidate_scores:
                        candidate_scores[node_id] = {"lexical": 0.0, "semantic": 0.0}
                    candidate_scores[node_id]["lexical"] = 1.0

    
    ranked_scores = []
    for node_id in candidate_scores:
        node_data = graph.G.nodes.get(node_id, {})
        entity_type = node_data.get('type')
        if entity_type not in ["function_definition", "class_definition"]:
            continue
        score = (0.6 * candidate_scores[node_id]["lexical"]) + (0.4 * candidate_scores[node_id]["semantic"])

        if "/tests/" in node_id.replace("\\", "/"):
            score -= 0.2
        out_calls = len([e for e in graph.G.successors(node_id) if graph.G.get_edge_data(node_id, e, {}).get('type') == 'calls'])
        score += min(out_calls, 5) * 0.02
        ranked_scores.append((score, node_id))
    
    ranked_scores.sort(reverse=True)
    for score, node_id in ranked_scores:
        if score > 0:
            return node_id
    return None
    
def answer_question(owner:str, repo_name:str, question:str) -> dict:
    vector_res = search(owner, repo_name, question, n_results=5)
    if not vector_res or not vector_res['documents'] or not vector_res['documents'][0]:
        return "No context found"
    graph = get_graph(owner, repo_name)
    seed_node = resolve_seed_node(graph, question, vector_res)

    traversed_nodes = []
    relationships = []
    code_snippets = []

    reverse_pattern = r'\b(who|what|which)\b.*?\b(calls?|inherits?|subclasses?)\b|\b(called by|callers?|used by|invoked by|subclasses of|inherits from|inherited by|where is)\b'
    is_reverse = bool(re.search(reverse_pattern, question, re.IGNORECASE))
    if any(kw in question.lower() for kw in ("execution flow", "call flow", "trace", "how does")):
        is_reverse = False
    traversal_dir = "in" if is_reverse else "out"

    if graph and seed_node:
        traversed_nodes = graph.bfs(seed_node, max_depth=4, max_nodes=15, direction=traversal_dir)
        if traversed_nodes:
            if is_reverse:
                items = []
                for n in traversed_nodes:
                    if n != seed_node:
                        edge = graph.G.get_edge_data(n, seed_node)
                        rel_type = edge.get('type', 'calls') if edge else 'references'
                        items.append(f"{graph.G.nodes[n].get('name', n)} ({rel_type})")
                relationships.append(f"Incoming relationships to '{graph.G.nodes[seed_node].get('name', seed_node)}': {', '.join(items)}")

            else:
                node_names = [graph.G.nodes[n].get('name', n) for n in traversed_nodes]
                relationships.append(f"Execution Call Flow: {' -> '.join(node_names)}")
            full_code_nodes = select_nodes_for_full_code(graph, seed_node, traversed_nodes, question, max_full_code=4)
            for node_name in traversed_nodes:
                node_data = graph.G.nodes.get(node_name, {})
                if node_name in full_code_nodes and node_data.get('code'):
                    code_snippets.append(
                        f"File: {node_data.get('file')}\nSymbol: {node_data.get('name')}\nCode:\n{node_data.get('code')}\n"
                    )
                else:
                    code_snippets.append(
                        f"Symbol: {node_data.get('name')} | File: {node_data.get('file')} | Lines: {node_data.get('start_line')}-{node_data.get('end_line')}"
                    )
    if not traversed_nodes:
            
        for i in range(len(vector_res['documents'][0])):
            doc = vector_res['documents'][0][i]
            meta = vector_res['metadatas'][0][i]
            
            code_snippets.append(f"File: {meta['file']}\nCode:\n{doc}\n")
            
            node_id = meta.get('id')
            if graph and node_id and graph.G.has_node(node_id):
                callers = [graph.G.nodes[nid].get('name', nid) for nid in graph.get_callers(node_id)]
                callees = [graph.G.nodes[nid].get('name', nid) for nid in graph.get_callees(node_id)]
                symbol_name = meta.get('name', node_id)
                if callers:
                    relationships.append(f"Functions that call '{symbol_name}': {', '.join(callers)}")
                if callees:
                    relationships.append(f"'{symbol_name}' calls these functions: {', '.join(callees)}")

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
    components and their relationships.
    
You must distinguish between:

1. FACTS DIRECTLY SUPPORTED BY THE PROVIDED REPOSITORY CONTEXT.
2. GENERAL PROGRAMMING KNOWLEDGE.

For repository-specific claims, do not rely on your pretrained knowledge
when the relevant source is absent from the provided context.

If a required file, symbol, implementation, or relationship is not present
in the provided context, explicitly state that it could not be verified.

Do not reconstruct missing repository code from general knowledge.

If general knowledge would help explain a missing concept, label it
explicitly as general knowledge and do not present it as evidence from
the repository.
    """
    user_prompt=f"""User Question: {question}
    
    <code_snippets>
    {chr(10).join(code_snippets)} 
    </code_snippets>
    
    <graph_relationships>
    {chr(10).join(relationships)}
    </graph_relationships>
    """
    provider = get_llm_provider()
    answer_text = provider.generate_response(system_prompt, user_prompt)
    sources = []
    for n in traversed_nodes:
        data = graph.G.nodes.get(n, {})
        sources.append({
            "symbol": data.get("name", n),
            "file": data.get("file"),
            "lines": f"{data.get('start_line')}-{data.get('end_line')}",
            "hydrated": "full_code" if n in full_code_nodes else "metadata"
        })
    return {
        "answer": answer_text,
        "seed_symbol": graph.G.nodes[seed_node].get("name", seed_node) if seed_node and graph.G.has_node(seed_node) else None,
        "traversal_direction": traversal_dir,
        "traversed_path": [graph.G.nodes[n].get("name", n) for n in traversed_nodes],
        "sources": sources
    }