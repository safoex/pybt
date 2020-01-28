from unittest import TestCase
from src.planner.belief_memory.belief_memory import BeliefMemory
from src.planner.build.planning_nodes import PlanningNodes


class TestPlanningNodes(TestCase):
    def setUp(self) -> None:
        self.memory = BeliefMemory({})
        self.nodes_builder = PlanningNodes(self.memory)

    def test_build_collection(self):
        yml = """
                root:
                    type: sequence
                    root: yes
                    children: [A1, C1, A2, C2]
                
                A1:
                    type: action
                    script: dafdg = 0
                    postconditions: 
                        -   prob: 0.5
                            action: a = 2
                        -   prob: 0.5
                            action: a = 0
                
                A2:
                    type: action
                    script: dafdg = 0
                    postconditions: 
                        -   prob: 0.5
                            action: a = 2
                        -   prob: 0.5
                            action: a = 0
                
                
                A3:
                    type: action
                    script: dasfdasd = 0
                    postconditions:
                        -   prob: 0.3
                            action: b = 2
                        -   prob: 0.7
                            action: b = -1
                C1:
                    type: condition
                    expression: a > 0
                    true_state: SUCCESS
                    false_state: FAILURE
                
                C2:
                    type: condition
                    expression: a > 0
                    true_state: SUCCESS
                    false_state: FAILURE
                    
                C3:
                    type: condition
                    expression: b > 0
                    true_state: SUCCESS
                    false_state: RUNNING
                """
        bt = self.nodes_builder.build_collection(yml, root_name='root')
        bt.memory = BeliefMemory({
            'a': 0,
            'b': 0
        })

        res = dict(bt.tick())
        print(res)
        self.assertEqual(0.75, res['F'].prob())
