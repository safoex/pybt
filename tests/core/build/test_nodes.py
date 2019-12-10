from unittest import TestCase
from src.core.nodes.leaf import Leaf, Condition, Action
from src.core.nodes.sequential import Sequential
from src.core.memory.memory import Memory
from definitions import State
from src.core.tree.behavior_tree import BehaviorTree
from src.core.build.yaml.nodes import Nodes

class TestNodes(TestCase):
    def setUp(self):
        self.memory = Memory()
        self.nodes_builder = Nodes(self.memory)

    def test_build_node_from_yaml(self):
        yml = """
        type: sequence
        children: []
        id: RRR
        """
        node = self.nodes_builder.build_from_yaml(yml)
        self.assertEqual(len(node.children), 0)
        self.assertEqual(node.id, 'RRR')
        self.assertEqual(node.skip_state, Sequential.Sequence)

    def test_build_action_from_yaml(self):
        yml = """
        type: action
        script: x = x + 1
        id: AAA
        """
        node = self.nodes_builder.build_from_yaml(yml)
        self.assertEqual(node.id, 'AAA')
        self.memory.add({'x': 1})
        node.tick()
        self.assertEqual(self.memory.vars['x'], 2)
        node.tick()
        self.assertEqual(self.memory.vars['x'], 3)

    def test_build_condition_from_yaml(self):
        yml = """
        type: condition
        expression: x == 2
        id: BBB
        true_state: SUCCESS
        false_state: FAILURE
        """
        node = self.nodes_builder.build_from_yaml(yml)
        self.assertEqual(node.id, 'BBB')
        self.memory.add({'x': 1})
        self.assertEqual(node.tick(), State.FAILURE)
        self.memory.set({'x': 2})
        self.assertEqual(node.tick(), State.SUCCESS)

    def test_build_collection_from_yaml(self):
        yml = """
        root:
            type: sequence
            children: [A, B]
        A:
            type: action
            script: x = x + 1.5
        B:
            type: condition
            expression: x > 3
            true_state: SUCCESS
            false_state: FAILURE
        """
        bt = self.nodes_builder.build_collection(yml, 'root')
        bt.memory.add({'x': 0})
        self.assertEqual(bt.nodes['B'].tick(), State.FAILURE)
        self.assertEqual(bt.tick(), State.FAILURE)
        self.assertEqual(bt.tick(), State.FAILURE)
        self.assertEqual(bt.tick(), State.SUCCESS)
        self.assertEqual(bt.memory.vars['x'], 4.5)
