from collections import deque
import networkx as nx

class RepoGraph:
    def __init__(self):
        self.G = nx.DiGraph()

    def add_entity(self, entity):
        self.G.add_node(entity['name'], **entity)

    def resolve_node(self, name:str, caller:str = None):
        if not name:
            return None
        if self.G.has_node(name):
            return name
        
        leaf = name.split('.')[-1]
        if '.' in name:
            for n in self.G.nodes():
                if n.endswith(f".{leaf}") and n != caller:
                    return n
        for n in self.G.nodes():
            if n == leaf and n != caller:
                return n
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
            src = self.resolve_node(caller)
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
        