import pathlib
from app.graph.store import RepoGraph
from app.parser.extractor import extract_entities
from app.parser.python_parser import parse_python_file

def process_repo(repo_path):
    repo_graph = RepoGraph()
    for file_path in pathlib.Path(repo_path).rglob('*.py'):
        try:
            tree = parse_python_file(file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            continue
        entities, relationships = extract_entities(tree, file_path)
        for entity in entities:
            repo_graph.add_entity(entity)
        for relationship in relationships:
            repo_graph.add_relationship(relationship)
    return repo_graph