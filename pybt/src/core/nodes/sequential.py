from pybt.src.core.nodes.control import ControlNode
from definitions import State


def SequentialInheriter(ControNodeClass):
    class _Sequential(ControNodeClass):
        Sequence = State.SUCCESS
        Fallback = State.FAILURE
        Skipper = State.RUNNING
        Names = {
            'sequence': Sequence,
            'fallback': Fallback,
            'skipper': Skipper
        }

        def __init__(self, skip_state, name, memory):
            super().__init__(name, memory)
            self.skip_state = skip_state

        def evaluate(self):
            for child in self.children:
                child_state = child.tick()
                if child_state != self.skip_state:
                    return child_state
            return self.skip_state

    return _Sequential


Sequential = SequentialInheriter(ControlNode)
