from unittest import TestCase
from src.planner.belief_memory.belief_memory import BeliefMemory
from src.planner.nodes.planning_node import PlanningSequential,PlanningLeaf
from tests.planner.memory.test_belief_memory import set_2a_3c
import copy

class TestPlanningNode(TestCase):
    def setUp(self) -> None:
        self.memory = BeliefMemory({
            'a': 0,
            'b': 0,
            'c': 0,
            'd': 0
        })
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

    def test_leaf_nodes(self):
        A1 = PlanningLeaf('a1', self.memory, self.a1)
        C1 = PlanningLeaf('c1', self.memory, self.c1)

        A1.tick()
        A1.tick()
        buckets = C1.tick()
        res = dict(buckets)
        P_C1 = res['S'].prob()
        self.assertEqual(0.5, P_C1)

    def test_sequence_node(self):
        mem = copy.deepcopy(self.memory)
        A1 = PlanningLeaf('a1', mem, self.a1)
        A2 = PlanningLeaf('a2', mem, self.a1)

        C1 = PlanningLeaf('c1', mem, self.c1)
        C2 = PlanningLeaf('c2', mem, self.c1)

        S1 = PlanningSequential(PlanningSequential.Sequence, 's1', mem)
        S1.children = [A1, C1, A2]
        res = dict(S1.tick())
        self.assertEqual(0.5, res['F'].prob())

        S1.children = [A1, C1, A2, C2]
        res = dict(S1.tick(with_memory=copy.deepcopy(self.memory)))
        self.assertEqual(0.75, res['F'].prob())

    def test_seq_and_fal_node(self):
        mem = copy.deepcopy(self.memory)
        A1 = PlanningLeaf('a1', mem, self.a1)
        A2 = PlanningLeaf('a2', mem, self.a1)

        C1 = PlanningLeaf('c1', mem, self.c1)
        C2 = PlanningLeaf('c2', mem, self.c1)

        S1 = PlanningSequential(PlanningSequential.Sequence, 's1', mem)
        F1 = PlanningSequential(PlanningSequential.Fallback, 'f1', mem)

        F1.children = [C2, A2]
        S1.children = [A1, F1, C2]
        res = dict(S1.tick())
        self.assertEqual(0.75, res['S'].prob())


