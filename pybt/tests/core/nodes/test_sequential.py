from unittest import TestCase
from pybt.src.core.nodes.leaf import Leaf, Condition, Action
from pybt.src.core.nodes.sequential import Sequential
from pybt.src.core.memory.memory import Memory
from definitions import State


class TestSequential(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()

    def test_empty(self):
        sequence = Sequential(Sequential.Sequence, 'test', self.memory)
        self.assertEqual(sequence.tick(), sequence.skip_state)

        skipper = Sequential(Sequential.Skipper, 'test', self.memory)
        self.assertEqual(skipper.tick(), skipper.skip_state)

        fallback = Sequential(Sequential.Fallback, 'test', self.memory)
        self.assertEqual(fallback.tick(), fallback.skip_state)

    def test_sequence_children(self):
        sequence = Sequential(Sequential.Sequence, 'test', self.memory)
        self.memory.add({'x': 0})
        self.memory.flush()
        action = Action('test2', self.memory, 'x = 2')
        condition = Condition('test3', self.memory, 'x == 1', State.SUCCESS, State.RUNNING)
        sequence.children = [condition, action]
        self.assertEqual(sequence.tick(), State.RUNNING)
        self.assertEqual(sequence.tick(), State.RUNNING)

        self.memory.set({'x': 1})
        self.assertEqual(sequence.tick(), State.SUCCESS)
        self.assertEqual(sequence.tick(), State.RUNNING)

        self.assertEqual(self.memory.vars['x'], 2)
        self.assertTrue('x' in self.memory.changes())

    def test_fallback_children(self):
        fallback = Sequential(Sequential.Fallback, 'test', self.memory)
        self.memory.add({'x': 0})
        self.memory.flush()
        action = Action('test2', self.memory, 'x = 2')
        condition = Condition('test3', self.memory, 'x == 1', State.SUCCESS, State.RUNNING)
        fallback.children = [condition, action]
        self.assertEqual(fallback.tick(), State.RUNNING)
        self.assertEqual(fallback.tick(), State.RUNNING)

        self.memory.set({'x': 1})
        self.assertEqual(fallback.tick(), State.SUCCESS)
        self.assertEqual(fallback.tick(), State.SUCCESS)

        self.memory.set({'x': 3})

        fallback.children[0] = Condition('test3', self.memory, 'x == 1', State.SUCCESS, State.FAILURE)

        self.assertEqual(fallback.tick(), State.SUCCESS)

        self.assertEqual(self.memory.vars['x'], 2)
        self.assertTrue('x' in self.memory.changes())



