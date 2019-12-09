from src.core.nodes.node import Node
from definitions import State


class Leaf(Node):
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
        except BaseException:
            return self.false_state


class Condition(Leaf):
    def __init__(self, name, memory, expression, true_state, false_state):
        super().__init__(name, memory, memory.build_condition(expression), true_state, false_state)
        self.expression = expression


class Action(Leaf):
    def __init__(self, name, memory, expression):
        super().__init__(name, memory, memory.build_action(expression), State.SUCCESS, State.FAILURE)
        self.expression = expression
