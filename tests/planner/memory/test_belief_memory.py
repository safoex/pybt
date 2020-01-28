from unittest import TestCase
from src.planner.belief_memory.belief_memory import BeliefMemory

def set_2a_3c(self):
    self.c1 = {
        'true_state': 'SUCCESS',
        'false_state': 'FAILURE',
        'expression': 'a > 0'
    }
    self.c2 = {
        'true_state': 'SUCCESS',
        'false_state': 'R',
        'expression': 'b > 0'
    }
    self.c3 = {
        'S': 'b > 1 and a == 0',
        'R': 'b < 0'
    }
    self.a1 = {
        'script': 'dafdg = 0',
        'postconditions': [
            {
                'prob': 0.5,
                'action': 'a = 2'
            },
            {
                'prob': 0.5,
                'action': 'a = 0'
            }
        ]
    }
    self.a2 = {
        'script': 'dafdadsg = 0',
        'postconditions': [
            {
                'prob': 0.3,
                'action': 'b = 2'
            },
            {
                'prob': 0.7,
                'action': 'b = -1'
            }
        ]
    }

class TestBeliefMemory(TestCase):
    def setUp(self) -> None:
        self.memory = BeliefMemory({})
        set_2a_3c(self)


    def test__is_leaf_a_condition(self):
        self.assertEqual(True, self.memory._is_leaf_a_condition(self.c1))
        self.assertEqual(True, self.memory._is_leaf_a_condition(self.c2))
        self.assertEqual(True, self.memory._is_leaf_a_condition(self.c3))
        self.assertEqual(False, self.memory._is_leaf_a_condition(self.a1))
        self.assertEqual(False, self.memory._is_leaf_a_condition(self.a2))

    def test_build_and_exec(self):
        a1 = self.memory.build(self.a1)
        a2 = self.memory.build(self.a2)
        c1 = self.memory.build(self.c1)
        c2 = self.memory.build(self.c2)
        c3 = self.memory.build(self.c3)

        memory = BeliefMemory({'a': 0, 'b': 1})

        res = dict(memory.exec(c1))
        self.assertTrue('R' not in res and 'S' not in res and 'F' in res)
        res = dict(memory.exec(a1))
        self.assertTrue('S' in res and 'R' not in res and 'F' not in res)
        res = dict(res['S'].exec(c1))
        self.assertTrue('R' not in res and 'S' in res and 'F' in res)
        print(dict(res['S'].exec(a2))['S'])
        res = dict(dict(res['S'].exec(a2))['S'].exec(c3))
        print(res)
        self.assertTrue('R' in res)
        self.assertEqual(0.35, sum(prob for state, prob in res['R'].states))

    def test_or(self):
        mem1 = BeliefMemory({'a': 1, 'b': 2}, 0.5)
        mem2 = BeliefMemory({'a': 0, 'b': 2}, 0.5)

        mem3 = mem1 | mem2
        self.assertTrue(isinstance(mem3, BeliefMemory))
        self.assertEqual(2, len(mem3.states))

        mem4 = BeliefMemory({'a': 1, 'b': 2}, 0.3)
        mem5 = mem4 | mem1
        mem5.simplify()
        self.assertEqual(1, len(mem5.states))
        self.assertEqual(0.8, mem5.states[0][1])

