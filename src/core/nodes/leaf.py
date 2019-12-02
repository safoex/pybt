from src.core.nodes.node import Node


class Leaf(Node):
    def __init__(self, name, memory, func, true_state, false_state):
        super().__init__(name, memory)
        self.func = func
        self.true_state = true_state
        self.false_state = false_state
    
    def evaluate(self):
        return self.true_state if self.func() else self.false_state
