from src.core.nodes.node import Node


class PlanningNode(Node):
    def __init__(self, name, memory, effects=None, postconditions=None, preconditions=None):
        super().__init__(name, memory)
        self.effects = effects
        self.postconditions = postconditions
        self.preconditions = preconditions

