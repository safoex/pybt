from src.core.memory.memory import Memory
from definitions import State
from src.core.nodes.sequential import Sequential

class BehaviorTree(object):
    TICK = 'TICK'
    ERASE = 'ERASE'
    REPLACE = 'REPLACE'
    INSERT = 'INSERT'
    
    def __init__(self, memory = None, root_node=None):
        self.memory = memory or Memory()
        self.root = root_node or Sequential(Sequential.Sequence, 'root', self.memory)
        self.nodes = {self.root.id: self.root}

    def execute(self, sample):
        if sample == BehaviorTree.tick:
            return self.tick()
        else:
            return self.apply_command(sample)
        
    def tick(self):
        """
        top down recursive tick propagation from the root node
        :return: None
        """
        try:
            return self.root.tick()
        except BaseException:
            return State.FAILURE

    def find_parent(self, node_name):
        def check_for_parent(node):
            if node_name in node.children:
                return node.id
            else:
                return None

        return self.root.dfs(check_for_parent)

    def apply_command(self, command):
        """
        :param command: a Python object with a command:
            ERASE: [nodes]
            REPLACE: [(old_node_name, new_node)]
            INSERT: {new_node_name, [(parent_node, i, new_node_def)]}
            Nodes are Python objects which have required fields but might contains extra info.
        :return: True if command successfully executed, False otherwise
        """
        success = True
        if BehaviorTree.ERASE in command:
            for n in command[BehaviorTree.ERASE]:
                if n in self.nodes:
                    self.nodes.pop(n)
                else:
                    success = False
                    raise RuntimeWarning("erasing node which does not exist")
        elif BehaviorTree.INSERT in command:
            cmd = command[BehaviorTree.INSERT]
            for parent, i, new_node in cmd:
                if new_node.id in self.nodes:
                    raise RuntimeWarning("an old node exists with the same name: " + n)
                if parent not in self.nodes:
                    raise RuntimeWarning("no parent node with the name: " + parent)
                parent_node = self.nodes[parent]
                parent_node.insert(new_node, i)
                self.nodes[new_node.id] = new_node
        elif BehaviorTree.REPLACE in command:
            cmd = command[BehaviorTree.REPLACE]
            for old_node_name, new_node in cmd:
                if old_node_name in self.nodes:
                    parent = self.find_parent(old_node_name)
                    i = self.nodes[parent].find(old_node_name)
                    self.apply_command({BehaviorTree.ERASE: [old_node_name]})
                    self.apply_command({BehaviorTree.INSERT: {new_node.id: [parent, i, new_node]}})

