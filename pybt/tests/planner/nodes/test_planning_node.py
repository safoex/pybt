from unittest import TestCase
from pybt.src.planner.belief_memory.belief_memory import BeliefMemory
from pybt.src.planner.nodes.planning_node import PlanningSequential,PlanningLeaf
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

    def test_leaf_nodes(self):
        A1 = PlanningLeaf('a1', self.memory, self.a1)
        C1 = PlanningLeaf('c1', self.memory, self.c1)
        mem = A1.tick()
        mem = mem.apply_delayed_actions()
        A1.tick(with_memory=mem)

        mem = mem.apply_delayed_actions()
        mem = C1.tick(with_memory=mem)
        P_C1 = mem.prob({mem.state_key: 'S'})
        self.assertEqual(0.5, P_C1)

    def test_sequence_node(self):
        mem = copy.deepcopy(self.memory)
        A1 = PlanningLeaf('a1', mem, self.a1)
        A2 = PlanningLeaf('a2', mem, self.a1)

        C1 = PlanningLeaf('c1', mem, self.c1)
        C2 = PlanningLeaf('c2', mem, self.c1)

        S1 = PlanningSequential(PlanningSequential.Sequence, 's1', mem)
        S1.children = [A1, C1, A2]
        mem = S1.tick()
        self.assertEqual(1, mem.prob({mem.state_key: 'F'}))
        mem = mem.apply_delayed_actions()
        mem = S1.tick(mem)
        self.assertEqual(0.5, mem.prob({mem.state_key: 'F'}))

        S1.children = [A1, C1, A2, C2]
        mem = copy.deepcopy(self.memory)
        mem = S1.tick(with_memory=mem)
        mem = mem.apply_delayed_actions()
        mem = S1.tick(mem)

        mem = mem.apply_delayed_actions()
        self.assertEqual(0.5, mem.prob({mem.state_key: 'F'}))

    def test_seq_and_fal_node(self):
        mem = BeliefMemory({'a': 0, 'b': 0})
        A1 = PlanningLeaf('a1', mem, self.a1)
        A2 = PlanningLeaf('a2', mem, self.a1)

        C1 = PlanningLeaf('c1', mem, self.c1)
        C2 = PlanningLeaf('c2', mem, self.c1)

        S1 = PlanningSequential(PlanningSequential.Sequence, 's1', mem)
        F1 = PlanningSequential(PlanningSequential.Fallback, 'f1', mem)

        F1.children = [C1, A2]
        S1.children = [F1, C2]
        res = S1.tick()
        res = res.apply_delayed_actions()
        res = S1.tick(res).apply_delayed_actions()
        res = S1.tick(res).apply_delayed_actions()
        self.assertEqual(0.75, res.prob({res.state_key: 'S'}))
    #
    #
