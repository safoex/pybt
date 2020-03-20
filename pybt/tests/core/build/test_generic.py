from unittest import TestCase
from pybt.src.core.build.yaml.generic import GenericBuilder
from pybt.src.core.build.yaml.nodes import Nodes
from pybt.src.core.build.yaml.memories import Memories
from pybt.src.core.tree.behavior_tree import BehaviorTree
from pybt.src.core.memory.memory import Memory
from pybt.src.core.io.io import IO, Task

class TestGenericBuilder(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.io = IO()
        self.memories = Memories(self.memory)
        self.bt = BehaviorTree('behavior_tree', self.memory)
        self.nodes = Nodes(self.memory)
        self.generic = GenericBuilder('builder', {'build'}, ['memory', 'vars', 'nodes', 'build'])
        self.io.reg(self.memories)
        self.io.reg(self.bt)
        self.io.reg(self.nodes)
        self.io.reg(self.generic)

    def test_bt(self):
        yml = """
        memory:
            vars:
                A: 2
                B: 3
                Z: 0
        nodes:
            Z:
                type: sequence
                children: [C, K]
                root: yep
            K:
                type: action
                script: Z += A * B
            C:
                type: condition
                expression: Z < 10 * A
                true_state: SUCCESS
                false_state: RUNNING
        """
        self.io.accept(Task(message=yml, keywords={'build'}, sender_name='test'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='heh'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='heh'))
        self.io.run_all()
        self.assertEqual(12, self.memory.vars['Z'])
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='heh'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='heh'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='heh'))
        self.io.run_all()
        self.assertEqual(24, self.memory.vars['Z'])

