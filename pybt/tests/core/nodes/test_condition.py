from unittest import TestCase
from pybt.src.core.nodes.leaf import Leaf, Condition, Action
from pybt.src.core.memory.memory import Memory
from definitions import State

class TestCondition(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()

    def test_simple_condition(self):
        self.memory.add({'x': 1})
        condition = Condition('test', self.memory, 'x == 1', State.SUCCESS, State.FAILURE)
        self.assertEqual(condition.tick(), State.SUCCESS)
        self.memory.set({'x': 2})
        self.assertEqual(condition.tick(), State.FAILURE)

    def test_empty_condition(self):
        self.memory.add({'x': 1})
        condition = Condition('test', self.memory, '', State.SUCCESS, State.FAILURE)
        self.assertEqual(condition.tick(), State.FAILURE)
        condition2 = Condition('test', self.memory, '', State.FAILURE, State.RUNNING)
        self.assertEqual(condition2.tick(), State.RUNNING)

