from src.core.nodes.node import Node


def ControlNodeInheriter(NodeClass):
    class _ControlNode(NodeClass):
        def __init__(self, name, memory):
            super().__init__(name, memory)

        def find(self, name):
            for i, child in enumerate(self.children):
                if child.id == name:
                    return i
            return None

        def insert(self, node, after=None):
            if isinstance(after, str):
                after = self.find(after)
            if after is None or not isinstance(after, int):
                after = -2
                self.children.insert(after + 1, node)
            elif isinstance(after, int) and after < 0:
                after = len(self.children)
            self.children.insert(after, node)

        def replace(self, node, old):
            index = self.find(old)
            if index is not None:
                self.children[index] = node

        def erase(self, old):
            index = self.find(old)
            if index is not None:
                self.children.pop(index)

    return _ControlNode


ControlNode = ControlNodeInheriter(Node)
