from unittest import TestCase
from pybt.src.planner.belief_memory.belief_memory import BeliefMemory


def set_2a_3c(self):
    self.c1 = {
        'id': 'c1',
        'true_state': 'SUCCESS',
        'false_state': 'FAILURE',
        'expression': 'a > 0'
    }
    self.c2 = {
        'id': 'c2',
        'true_state': 'SUCCESS',
        'false_state': 'R',
        'expression': 'b > 0'
    }
    self.c3 = {
        'id': 'c3',
        'S': 'b > 1 and a == 0',
        'R': 'b < 0'
    }
    self.a1 = {
        'id': 'a1',
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
        'id': 'a2',
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

        res = memory.exec(c1)
        self.assertEqual(1, res.prob({res.state_key: 'F'}))
        res = memory.exec(a1).apply_delayed_actions()
        self.assertEqual(1, res.prob({res.state_key: 'S'}))

        res = res.exec(c1)
        self.assertTrue(res.prob({res.state_key: 'S'}) > 0 and res.prob({res.state_key: 'F'}) > 0)
        res = res.select_whether(lambda s: s[res.state_key] != 'S') + \
              res.select_whether(lambda s: s[res.state_key] == 'S').exec(self.a2).apply_delayed_actions()
        P_S = res.exec(self.c2).prob({res.state_key: 'R'})
        self.assertEqual(0.35, P_S)

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
