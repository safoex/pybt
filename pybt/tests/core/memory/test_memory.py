from unittest import TestCase
from pybt.src.core.memory.memory import Memory


class TestMemory(TestCase):
    def setUp(self):
        self.memory = Memory()


class TestMemoryExec(TestMemory):
    def test_exec(self):
        self.memory.exec("x = 3")
        self.assertEqual(self.memory.vars['x'], 3)

    def test_exec_service(self):
        self.memory.exec_service('set', {'x': 3})
        self.assertEqual(self.memory.vars['x'], 3)

    def test_exec_function_with_result(self):
        self.memory.exec('x = 3')
        self.memory.exec('y = 5')
        self.memory.exec('K = lambda a, b: a + b')
        self.assertEqual(8, self.memory.exec_function_with_return('K(x,y)'))
        self.assertEqual(10, self.memory.exec_function_with_return('K(z,t)', {'z': 7, 't': 3}))


class TestMemoryUpdate(TestMemory):
    def test_set(self, test_in=False):
        self.memory.set({'x': 3})
        self.assertEqual(self.memory.vars['x'], 3)
        if test_in:
            self.assertTrue('x' in self.memory.changes())
        else:
            self.assertTrue('x' not in self.memory.changes())

    def test_add(self):
        self.memory.add({'x': 3})
        self.assertEqual(self.memory.vars['x'], 3)
        self.assertTrue('x' not in self.memory.changes())

    def test_exec(self):
        self.test_add()
        self.memory.exec('x = 4')
        self.assertEqual(self.memory.vars['x'], 4)
        self.memory.exec_service('update')
        self.assertTrue('x' in self.memory.changes())

    def test_flush(self):
        self.test_exec()
        self.memory.flush()
        self.assertTrue('x' not in self.memory.changes())
        self.test_set(test_in=True)
        self.memory.flush()
        self.assertTrue('x' not in self.memory.changes())


class TestMemoryUtility(TestMemory):
    def test_unindent(self):
        block = """
        x = 1;
        y = 2;
        """
        cutted = """
x = 1;
y = 2;
        """
        self.assertEqual(Memory.unindent(block).strip(), cutted.strip())


class TestMemoryBuild(TestMemory):
    def test_build_action(self):
        self.memory.add({'x': 0})
        self.memory.flush()
        action = self.memory.build_action('x = 3')
        action()
        self.assertEqual(self.memory.vars['x'], 3)
        self.assertTrue('x' in self.memory.changes())

    def test_build_condition(self):
        self.memory.add({'x': 0})
        self.memory.flush()
        condition = self.memory.build_condition('x == 0')
        self.assertTrue(condition())
        self.memory.set({'x': 1})
        self.assertFalse(condition())

    def test_build_action_multiline(self):
        self.memory.add({'x': 0, 'y': 0})
        self.memory.flush()
        action_text = """
        x = 1;
        y = 2;
        """
        action = self.memory.build_action(action_text)
        action()
        self.assertEqual(self.memory.vars['x'], 1)
        self.assertEqual(self.memory.vars['y'], 2)
        self.assertTrue('x' in self.memory.changes())
        self.assertTrue('y' in self.memory.changes())

    def test_build_condition_multiline(self):
        self.memory.add({'x': 1, 'y': 2})
        self.memory.flush()
        condition_text = """
        x == \
        y
        """
        condition = self.memory.build_condition(condition_text)
        self.assertFalse(condition())
        self.memory.set({'x': 2})
        self.assertTrue(condition())