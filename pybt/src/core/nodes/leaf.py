from pybt.src.core.nodes.node import Node
from definitions import State


def LeafNodeInheriter(NodeClass):
    class _Leaf(NodeClass):
        def __init__(self, name, memory, func, true_state, false_state):
            super().__init__(name, memory)
            self.func = func
            self.true_state = true_state
            self.false_state = false_state

        def evaluate(self):
            try:
                res = self.func()
                if res is None:
                    return self.true_state
                return self.true_state if res else self.false_state
            except BaseException as e:
                print('exception in ' + self.id, ": ", e)
                return self.false_state
    return _Leaf


def ConditionNodeInheriter(LeafClass):
    class _Condition(LeafClass):
        def __init__(self, name, memory, expression, true_state, false_state):
            super().__init__(name, memory, memory.build_condition(expression), true_state, false_state)
            self.expression = expression
    return _Condition


def ActionNodeInheriter(LeafClass):
    class _Action(LeafClass):
        def __init__(self, name, memory, expression):
            super().__init__(name, memory, memory.build_action(expression), State.SUCCESS, State.FAILURE)
            self.expression = expression
    return _Action


Leaf = LeafNodeInheriter(Node)
Condition = ConditionNodeInheriter(Leaf)
Action = ActionNodeInheriter(Leaf)