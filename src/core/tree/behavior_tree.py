from src.core.memory.memory import Memory
from definitions import State
from src.core.nodes.sequential import Sequential
from src.core.io.io import Channel, Task
import copy


class BehaviorTree(Channel):
    TICK = 'TICK'
    ERASE = 'ERASE'
    REPLACE = 'REPLACE'
    INSERT = 'INSERT'

    def __init__(self, name='behavior_tree', memory=None, root_node=None, SequentialClass=Sequential):
        super().__init__(name, keywords={'behavior_tree'})
        self.memory = memory or Memory()
        self.root = root_node or SequentialClass(SequentialClass.Sequence, 'root', self.memory)
        self.nodes = {self.root.id: self.root}

    def execute(self, sample):
        if sample == BehaviorTree.TICK:
            return self.tick()
        else:
            return self.apply_command(sample)

    def tick(self):
        """
        top down recursive tick propagation from the root node
        :return: None
        """
        return self.root.tick()

    def find_parent(self, node_name):
        def check_for_parent(node):
            if node_name in [c.id for c in node.children]:
                return node.id
            else:
                return None

        return self.root.dfs(check_for_parent)

    def apply_command(self, command):
        """
        :param command: a Python object with a command:
            ERASE: [nodes]
            REPLACE: [(old_node_name, new_node)]
            INSERT: [(parent_node, i, new_node_def)]
            Nodes are Python objects which have required fields but might contains extra info.
        :return: True if command successfully executed, False otherwise
        """
        if BehaviorTree.ERASE in command:
            for n in command[BehaviorTree.ERASE]:
                if n in self.nodes:
                    self.nodes.pop(n)
                else:
                    raise RuntimeWarning("erasing node which does not exist")
        elif BehaviorTree.INSERT in command:
            cmd = command[BehaviorTree.INSERT]
            for parent, i, new_node in cmd:
                if new_node.id in self.nodes:
                    raise RuntimeWarning("an old node exists with the same name: " + new_node.id)
                if parent not in self.nodes:
                    raise RuntimeWarning("no parent node with the name: " + parent)
                parent_node = self.nodes[parent]
                parent_node.insert(new_node, i)
                self.nodes[new_node.id] = new_node
                # now add reqursively children
                if len(new_node.children) > 0:
                    def adder(_n):
                        self.nodes[_n.id] = _n

                    new_node.dfs(adder)
        elif BehaviorTree.REPLACE in command:
            cmd = command[BehaviorTree.REPLACE]
            for old_node_name, new_node in cmd:
                if old_node_name in self.nodes:
                    parent = self.find_parent(old_node_name)
                    i = self.nodes[parent].find(old_node_name)
                    self.apply_command({BehaviorTree.ERASE: [old_node_name]})
                    self.apply_command({BehaviorTree.INSERT: {new_node.id: [parent, i, new_node]}})

    def on_message(self, task):
        if task.sender_name == self.name:
            return
        if task.message == BehaviorTree.TICK:
            return Task(message=self.execute(task.message), sender_name=self.name,
                        keywords={'behavior_tree', 'state'})
        if 'new' in task.keywords:
            self.memory = task.message.memory
            self.nodes = task.message.nodes
            self.root = task.message.root
        elif 'replace' in task.keywords:
            self.apply_command({BehaviorTree.REPLACE: task.message})
        elif 'insert' in task.keywords:
            self.apply_command({BehaviorTree.INSERT: task.message})
        elif 'erase' in task.keywords:
            self.apply_command({BehaviorTree.ERASE: task.message})

        return Task(message=self, sender_name=self.name, keywords={'behavior_tree', 'changed'})

    def path_from_root(self, node):
        stack = []
        result = []

        def dfs(n):
            stack.append(n)
            if n.id == node.id:
                nonlocal result
                result = copy.deepcopy(stack)
                return True
            else:
                for c in n.children:
                    if dfs(c):
                        return True
            stack.pop(-1)
            return False

        dfs(self.root)
        return result

    def find_ncr(self, n1, n2):
        p1 = self.path_from_root(n1)
        p2 = self.path_from_root(n2)
        ncr = self.root.id
        for i, c1 in enumerate(p1):
            if i >= len(p2) or c1.id != p2[i]:
                ncr = p1[i - 1]
                break
        return ncr
