from src.core.build.yaml.nodes import Nodes
from src.planner.PlanningBehaviorTree import PlanningBehaviorTree
from src.planner.nodes.planning_node import PlanningLeaf, PlanningSequential
import copy

class PlanningNodes(Nodes):
    def __init__(self, memory):
        super().__init__(memory, PlanningBehaviorTree)

    def build_action_from_python(self, node, _id):
        self._check_and_raise(node, 'script')
        self._check_and_raise(node, 'postconditions')
        return PlanningLeaf(_id, self.memory, copy.copy(node))

    def build_condition_from_python(self, node, _id):
        params = ['expression', 'true_state', 'false_state']
        self._check_and_raise(node, params, ' for node ' + _id)
        return PlanningLeaf(_id, self.memory, copy.copy(node))

    def build_sequential_from_python(self, node, _id, _type):
        seq = PlanningSequential(skip_state=PlanningSequential.Names[_type], name=_id, memory=self.memory)
        self._check_and_raise(node, 'children', ' for node ' + _id)
        seq.children = node['children']
        return seq

