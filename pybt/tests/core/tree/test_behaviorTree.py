from unittest import TestCase
from pybt.src.core.nodes.leaf import Condition, Action
from pybt.src.core.memory.memory import Memory
from definitions import State
from pybt.src.core.tree.behavior_tree import BehaviorTree

class TestBehaviorTree(TestCase):
    def setUp(self) -> None:
        self.bt = BehaviorTree(Memory())

    def test_empty_tick(self):
        self.assertEqual(self.bt.tick(), State.SUCCESS)

    def test_insert_node(self):
        action = Action('test', self.bt.memory, 'x = x + 1')
        self.bt.memory.add({'x': 0})
        self.bt.execute({self.bt.INSERT: [('root', 0, action)]})
        self.assertEqual(self.bt.tick(), State.SUCCESS)
        self.assertTrue('x' in self.bt.memory.changes())
        self.assertEqual(self.bt.memory.vars['x'], 1)
        condition = Condition('test2', self.bt.memory, 'x == 3', State.SUCCESS, State.FAILURE)
        self.bt.execute({self.bt.INSERT: [('root', -1, condition)]})
        self.assertEqual(self.bt.tick(), State.FAILURE)
        self.assertEqual(self.bt.tick(), State.SUCCESS)
        self.assertEqual(self.bt.memory.vars['x'], 3)
