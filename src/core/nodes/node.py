from definitions import State


class Node:
    def __init__(self, name, memory, no_add=False):
        self.id = name
        self.memory = memory
        if not no_add:
            self.memory.add({self.state_key(): 4})
        self.children = []
        self._after_tick = None
        self._before_tick = None

    def state_key(self):
        return State.Key(self.id)

    def state(self):
        return self.memory.vars[self.state_key()]

    def tick(self):
        if self._before_tick:
            self._before_tick(self)
        state = self.evaluate()
        self.memory.set({self.state_key(): state})
        if self._after_tick:
            self._after_tick(self, state)
        return state

    def evaluate(self):
        pass

    def dfs(self, handler):
        res = handler(self)
        if res is not None:
            return res
        if len(self.children):
            for child in self.children:
                res = child.dfs(handler)
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
