from src.core.nodes.node import Node
from src.core.nodes.control import ControlNode
from definitions import State
from src.core.nodes.leaf import LeafNodeInheriter
from src.core.nodes.control import ControlNodeInheriter
from src.core.nodes.sequential import SequentialInheriter
from bsagr import BeliefStateSimple as BSS


class PlanningNode(Node):
    def __init__(self, name, memory):
        super().__init__(name, memory, no_add=True)

    def tick(self, with_memory=None, starting_from=0):
        if with_memory is None:
            with_memory = self.memory
        self._before_tick()
        buckets = self.evaluate(with_memory, starting_from)
        self._after_tick()
        return buckets

    def evaluate(self, with_memory=None, starting_from=0):
        return [(State.SUCCESS, BSS({})),
                (State.FAILURE, BSS({})),
                (State.RUNNING, BSS({}))]


class PlanningLeaf(PlanningNode):
    def __init__(self, name, memory, func):
        super().__init__(name, memory)
        self.func = memory.build(func)

    def evaluate(self, with_memory=None, starting_from=0):
        memory = with_memory or self.memory
        return memory.exec(self.func)


PlanningControlNode = ControlNodeInheriter(PlanningNode)


class PlanningSequential(SequentialInheriter(PlanningControlNode)):
    Sequence = 'S'
    Fallback = 'F'
    Skipper = 'R'
    Names = {
        'sequence': Sequence,
        'fallback': Fallback,
        'skipper': Skipper
    }

    def __init__(self, skip_state, name, memory):
        super().__init__(skip_state, name, memory)

    def evaluate(self, with_memory=None, starting_from=0):
        memory = with_memory or self.memory
        child = self.children[starting_from]
        res = list(child.tick(memory))
        buckets = dict(res)
        if self.skip_state in buckets and starting_from < len(self.children) - 1:
            nexts = dict(self.tick(buckets[self.skip_state], starting_from + 1))
            # join buckets
            prevs = buckets
            result = {}
            states = {'S', 'F', 'R'}
            states.remove(self.skip_state)
            for state in states:
                if state in prevs and state in nexts:
                    result[state] = prevs[state] | nexts[state]
                elif state in prevs:
                    result[state] = prevs[state]
                elif state in nexts:
                    result[state] = nexts[state]

            if self.skip_state in nexts:
                result[self.skip_state] = nexts[self.skip_state]
            res = list(result.items())

        return res
