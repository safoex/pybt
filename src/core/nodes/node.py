from src.core.defs import State
class Node: 
    def __init__(self, name, memory):
        self.id = name
        self.memory = memory
        self.memory.add({self.state_key(): State.RUNNING})
        self.children = []
    
    def state_key(self):
        return State.Key(self.id)
    
    def state(self):
        return self.memory.vars[self.state_key()]
    
    def tick(self):
        self._before_tick()
        state = self.evaluate()
        self.memory.set({self.state_key(): state})
        self._after_tick()
        return state
    
    def evaluate(self):
        pass
    
    def _before_tick(self):
        pass
    
    def _after_tick(self):
        pass
    
    def _dfs(self, handler):
        if handler(self):
            return True
        if len(self.children):
            for child in self.children:
                if child._dfs(self):
                    return True
        else:
            return False
            
    def _bfs(self, handler):
        current = [self]
        nexts = []
        while len(current) != 0:
            for node in current:
                if handler(node):
                    return True
                else:
                    nexts += node.children
            
            current, nexts = nexts, current
            nexts.clear()
        return False
