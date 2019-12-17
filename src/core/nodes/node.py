from definitions import State


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

    def dfs(self, handler):
        res = handler(self)
        if res is not None:
            return res
        if len(self.children):
            for child in self.children:
                res = child.dfs(self)
                if res is not None:
                    return res
        else:
            return None

    def _bfs(self, handler):
        current = [self]
        nexts = []
        while len(current) != 0:
            for node in current:
                res = handler(node)
                if res is not None:
                    return res
                else:
                    nexts += node.children

            current, nexts = nexts, current
            nexts.clear()
        return None
