from src.core.nodes.control import ControlNode
from src.core.defs import State


class Sequential(ControlNode):
    Sequence = State.FAILURE
    Fallback = State.SUCCESS
    Skipper = State.RUNNING

    def __init__(self, return_state, name, memory):
        super().__init__(name, memory)
        self.return_state = return_state
    
    def evaluate(self):
        for child in self.children:
            child_state = child.tick()
            if child_state != self.return_state:
                return child_state
        return self.return_state
