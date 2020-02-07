from src.core.nodes.node import Node
from src.core.nodes.control import ControlNode
from definitions import State
from src.core.nodes.leaf import LeafNodeInheriter
from src.core.nodes.control import ControlNodeInheriter
from src.core.nodes.sequential import SequentialInheriter
from bsagr import BeliefStateSimple as BSS
import copy


class PlanningNode(Node):
    StateKey = '_S'

    def __init__(self, name, memory):
        super().__init__(name, memory, no_add=True)

    def tick(self, with_memory=None, starting_from=0):
        if with_memory is None:
            with_memory = self.memory
        if self._before_tick:
            self._before_tick(self)
        buckets = self.evaluate(with_memory, starting_from)
        if self._after_tick:
            self._after_tick(self, buckets)
        return buckets

    def evaluate(self, with_memory=None, starting_from=0):
        return type(with_memory or self.memory)()


class PlanningLeaf(PlanningNode):
    def __init__(self, name, memory, func):
        super().__init__(name, memory)
        func['id'] = name
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
        if starting_from >= len(self.children) or len(memory.states) == 0:
            # print(starting_from, '', copy.deepcopy(memory).apply({memory.action_key: []}))
            return memory

        child = self.children[starting_from]
        # print('before before', [len(s[memory.action_key]) for s, p in memory.states if memory.action_key in s])

        res = child.tick(memory)
        # print('before', [len(s[res.action_key]) for s, p in res.states])
        skip_states = res.select_whether(lambda s: s[res.state_key] == self.skip_state)
        ret_states = res.select_whether(lambda s: s[res.state_key] != self.skip_state)
        res = ret_states + self.tick(skip_states, starting_from + 1)
        # print('after', [len(s[res.action_key]) for s, p in res.states])
        return res