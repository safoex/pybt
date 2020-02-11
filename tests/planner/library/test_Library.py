from unittest import TestCase
from src.planner.library.Library import TemplateLibrary
from ruamel import yaml
from src.planner.nodes.planning_node import PlanningSequential
import copy
from src.planner.belief_memory.belief_memory import BeliefMemory


class TestTemplateLibrary(TestCase):
    def setUp(self) -> None:
        self.lib = TemplateLibrary()
        with open("../build/yaml/domain.yaml") as df:
            self.domain = df.read()
        with open("../build/yaml/templates.yaml") as tf:
            self.templates = tf.read()

    def load(self):
        self.lib.load_templates(self.templates)
        self.lib.load_domain(self.domain)

    def default_state(self):
        res = copy.deepcopy(self.lib.vars)
        res.update(self.lib.constants)
        return res

    def test_load(self):
        self.load()

    def test_compile_nodes(self):
        self.load()

        _id, nodes = self.lib.compile_node_for_runtime("t/goto", {"location": "kitchen"})
        self.assertTrue(_id in nodes['nodes'])

        pl = self.lib.compile_node_for_planning("e0", "t/goto", {"location": "kitchen"})
        self.assertTrue(isinstance(pl, PlanningSequential))

    def test_get_best_templates_for_condition(self):
        self.load()
        state = BeliefMemory(self.default_state())
        bests = self.lib.get_best_templates_for_condition({
            'type': 'condition',
            'true_state': 'SUCCESS',
            'false_state': 'FAILURE',
            'expression': 'grasped == can',
            'var': 'grasped',
            'val': 'can'
        }, None, state)
        _id = bests[0][1]
        nodes = bests[0][2]['nodes']
        self.assertTrue(_id in nodes)
        a_id = '_' + _id + "_action"
        self.assertTrue(a_id in nodes)
        self.assertTrue(
            any('grasped' in postc and postc['grasped'] == 'can' for postc in nodes[a_id]['postconditions'])
        )


