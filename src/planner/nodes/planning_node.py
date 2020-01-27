from src.core.nodes.node import Node
from src.core.nodes.control import ControlNode
from definitions import State
from src.core.nodes.leaf import LeafNodeInheriter
from src.core.nodes.control import ControlNodeInheriter
from src.core.nodes.sequential import SequentialInheriter
from bsagr import BeliefStateSimple as BSS


class PlanningNode(Node):
    def __init__(self, name, memory, postconditions=None, preconditions=None):
        super().__init__(name, memory)
        self.postconditions = postconditions
        self.preconditions = preconditions

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
    def __init__(self, name, memory, func, true_state, false_state):
        super().__init__(name, memory)
        self.func = memory.build(func)
        self.true_state = true_state
        self.false_state = false_state

    def evaluate(self, with_memory=None, starting_from=0):
        memory = with_memory or self.memory
        return memory.exec(self.func)


PlanningControlNode = ControlNodeInheriter(PlanningNode)


class PlanningSequential(SequentialInheriter(PlanningControlNode)):
    def __init__(self, skip_state, name, memory):
        super().__init__(skip_state, name, memory)

    def evaluate(self, with_memory=None, starting_from=0):
        memory = with_memory or self.memory
        child = self.children[starting_from]
        buckets = child.tick(memory)
        if self.skip_state not in buckets or len(self.chilrden) == starting_from + 1:
            return buckets
        else:
            next_buckets = self.tick(buckets[self.skip_state], starting_from + 1)
            # join buckets
            prevs = {k: v for k, v in buckets}
            nexts = {k: v for k, v in next_buckets}
            result = {}
            for state in ['S', 'F', 'R']:
                if state in prevs and state in nexts:
                    result[state] = prevs[state] | prevs[nexts]
                elif state in prevs:
                    result[state] = prevs[state]
                elif state in nexts:
                    result[state] = nexts[state]
            return result
