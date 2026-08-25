import networkx as nx

class RepoGraph:
    def __init__(self):
        self.G = nx.DiGraph()

    def add_entity(self, entity):
        self.G.add_node(entity['name'], **entity)

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
            if self.G.has_node(caller) and self.G.has_node(callee):
                self.G.add_edge(caller, callee, **relationship)
    
    def get_callers(self, func_name):
        return list(self.G.predecessors(func_name))
    
    def get_callees(self, func_name):
        return list(self.G.successors(func_name))