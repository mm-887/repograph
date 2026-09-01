import pathlib
import os
from app import config
from app.graph.store import RepoGraph
from app.parser.extractor import extract_entities
from app.parser.python_parser import parse_python_file
from app.graph.vector_store import index_entities

def process_repo(owner, repo_name):
    repo_path = os.path.join(config.REPOS_DIR, owner, repo_name)
    repo_graph = RepoGraph()
    all_entities = []
    all_relationships = []

    # Pass 1: Parse all files and add all entities (nodes) to the graph
    for file_path in pathlib.Path(repo_path).rglob('*.py'):
        try:
            tree = parse_python_file(file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            continue
        entities, relationships = extract_entities(tree, str(file_path))
        for entity in entities:
            repo_graph.add_entity(entity)
        all_entities.extend(entities)
        all_relationships.extend(relationships)

    # Pass 2: Now that ALL nodes exist, resolve and add edges
    for relationship in all_relationships:
        repo_graph.add_relationship(relationship)
            
    index_entities(owner, repo_name, all_entities)
    return repo_graph