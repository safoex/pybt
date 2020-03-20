from unittest import TestCase
from pybt.src.core.nodes.leaf import Leaf, Condition, Action
from pybt.src.core.memory.memory import Memory
from definitions import State



class TestAction(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()

    def test_simple_action(self):
        self.memory.add({'x': 1})
        self.memory.flush()
        self.assertEqual(len(self.memory.changes()), 0)
        action = Action('test', self.memory, 'x = 2')
        self.assertEqual(action.tick(), State.SUCCESS)
        self.assertTrue('x' in self.memory.changes())
        self.assertEqual(self.memory.vars['x'], 2)

    def test_broken_action(self):
        self.memory.add({'x': 1})
        self.memory.flush()
        self.assertEqual(len(self.memory.changes()), 0)
        action = Action('test', self.memory, 'x = y/2')
        self.assertEqual(action.tick(), State.FAILURE)



class TestLeafs(TestAction):
    def test_action_and_condition(self):
        self.memory.add({'x': 1})
        self.memory.flush()
        action = Action('test', self.memory, 'x = 2')
        condition = Condition('test2', self.memory, 'x == 2', State.SUCCESS, State.RUNNING)
        self.assertEqual(condition.tick(), State.RUNNING)
        self.assertEqual(action.tick(), State.SUCCESS)
        self.assertEqual(condition.tick(), State.SUCCESS)
