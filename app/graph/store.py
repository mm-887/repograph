from collections import deque
import networkx as nx

class RepoGraph:
    def __init__(self):
        self.G = nx.DiGraph()
        self.name_index = {}

    def add_entity(self, entity):
        self.G.add_node(entity['id'], **entity)
        self.name_index.setdefault(entity['name'], []).append(entity['id'])

    def resolve_node(self, name:str, caller:str = None):
        if not name:
            return None
        if name in self.name_index:
            candidates = self.name_index[name]
            if len(candidates) == 1:
                return candidates[0]
            else:
                if caller:
                    caller_file = caller.split(':')[0]
                    for node_id in candidates:
                        if node_id.startswith(f"{caller_file}:"):
                            return node_id
                candidates = [c for c in candidates if "/tests/" not in c.replace("\\", "/") and "test_" not in c]
                if len(candidates) == 1:
                    return candidates[0]

        leaf = name.split('.')[-1]
        if caller:
            caller_class = caller.split(':')[1].split('.')[0]
            scoped_name = f"{caller_class}.{leaf}"
            if scoped_name in self.name_index:
                return self.name_index[scoped_name][0]

        if '.' in name:
            matches = []
            for node_id, node_data in self.G.nodes(data=True):
                if node_data.get('name','').endswith(f".{leaf}") and node_id != caller:
                    matches.append(node_id)
            if len(matches) == 1:
                return matches[0]
            if matches and caller:
                caller_file = caller.split(':')[0]
                for match in matches:
                    if match.startswith(f"{caller_file}:"):
                        return match
            return None
            
        matches = []
        for node_id, node_data in self.G.nodes(data=True):
            if node_data.get('name','') == leaf and node_id != caller:
                matches.append(node_id)
        if len(matches) == 1:
            return matches[0]
        if matches and caller:
            caller_file = caller.split(':')[0]
            for match in matches:
                if match.startswith(f"{caller_file}:"):
                    return match
        return None
    def add_relationship(self, relationship):
        caller = relationship['from']
        callee = relationship['to']
        rel_type = relationship.get('type')
        if rel_type == 'imports':
            if not self.G.has_node(caller):
                self.G.add_node(caller, type='module')
            if not self.G.has_node(callee):
                self.G.add_node(callee, type='external_module')
            self.G.add_edge(caller, callee, **relationship)
        else:
            src = caller if self.G.has_node(caller) else None
            dst = self.resolve_node(callee, caller = src) 
            if src and dst:
                self.G.add_edge(src, dst, **relationship)
    
    def get_callers(self, func_name):
        return list(self.G.predecessors(func_name))
    
    def get_callees(self, func_name):
        return list(self.G.successors(func_name))

    def bfs(self, seed_node, max_depth:int = 3, max_nodes:int = 20):
        if not self.G.has_node(seed_node):
            return None
        ordered_nodes = [seed_node]
        visited = {seed_node}
        q = deque([(seed_node,0)])
        while q and len(visited) < max_nodes:
            curr = q.popleft()
            depth = curr[1]
            if depth >= max_depth:
                continue
            curr_node = curr[0]
            for neighbor in self.G.neighbors(curr_node):
                edge_data = self.G.get_edge_data(curr_node, neighbor)
                if edge_data.get('type') == 'calls':
                    if neighbor not in visited:
                        visited.add(neighbor)
                        ordered_nodes.append(neighbor)
                        q.append((neighbor, depth + 1))
        return ordered_nodes
        