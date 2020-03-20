from unittest import TestCase
from pybt.src.core.build.yaml.memories import Memories
from pybt.src.core.io.io import IO, Task
from pybt.src.core.memory.memory import Memory


class TestMemories(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.memories = Memories(self.memory)
        self.io = IO()
        self.io.reg(self.memories)

    def test_variables(self):
        yml = """
        vars:
            A: '5'
            B: '"abc"'
            D: str()
            C: '6'
        """
        self.io.accept(Task(yml, 'test', {'memory'}))
        self.io.run_all()
        self.assertEqual(self.memory.vars['A'] + self.memory.vars['C'], 11)

    def test_exec(self):
        yml = """
        exec: "X = 5"
        """
        self.io.accept(Task(yml, 'test', {'memory'}))
        self.io.run_all()
        self.assertEqual(self.memory.vars['X'], 5)

    def test_memory(self):
        yml = """
        memory:
            execute:
                - X = 5
                - Z = 3
            vars:
                x: X + Z
                z: X - Z
        """
        self.io.accept(Task(yml, 'test', {'memory'}))
        self.io.run_all()
        self.assertEqual(self.memory.vars['X'] * 2, self.memory.vars['x'] + self.memory.vars['z'])
