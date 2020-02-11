from unittest import TestCase
from src.planner.belief_memory.belief_memory import BeliefMemory
from src.planner.build.planning_nodes import PlanningNodes
from src.core.build.yaml.templates import Templates
from src.core.build.yaml.memories import Memories
from src.core.build.yaml.nodes import Nodes
from src.core.tree.behavior_tree import BehaviorTree
from src.core.build.yaml.generic import GenericBuilder
from src.core.memory.memory import Memory
from src.core.build.yaml.imports import Import
from src.core.io.io import Task, IO, Channel, Hook
import copy
from ruamel import yaml
from src.planner.PlanningBehaviorTree import PlanningBehaviorTree
import itertools


class TestPlanningBehaviorTree(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.belief_memory = BeliefMemory([])
        self.planning_io = IO()
        self.planning_nodes = PlanningNodes(self.belief_memory)
        self.planning_import = Import(self.memory)
        self.planning_memories = Memories(self.memory)
        self.planning_templates = Templates(self.memory)
        self.planning_generic = GenericBuilder('builder', {'build'},
                                               ['build', 'import', 'memory', 'templates', 'vars', 'nodes'])
        self.planning_io.reg(self.planning_nodes)
        self.planning_io.reg(self.planning_generic)
        self.planning_io.reg(self.planning_templates)
        self.planning_io.reg(self.planning_import)
        self.planning_io.reg(self.planning_memories)

        self.pbt = PlanningBehaviorTree()
        self.planning_io.reg(self.pbt)

    def load_templates(self, templates_file):
        task = Task(message=copy.deepcopy(templates_file), sender_name='anonymous', keywords={'build'})
        self.planning_io.accept(task)
        self.planning_io.run_all()

    def build_tree(self, nodes):
        task = Task(message=copy.deepcopy(nodes), sender_name='anonymous', keywords={'build'})
        self.planning_io.accept(task)
        self.planning_io.run_all()

    def build_tree_example(self):

        with open("build/yaml/templates.yaml") as tf:
            self.load_templates(tf.read())
        nodes = """
        nodes:
            root:
                type: t/put
                root: yes
                object: can
                place: table2
        """
        self.build_tree(nodes)

    def test_build_tree(self):
        self.build_tree_example()
        self.assertTrue('root' in self.pbt.nodes)

    def get_state(self):
        with open("build/yaml/domain.yaml") as df:
            yaml_domain = yaml.safe_load(df)
        state = BeliefMemory(yaml_domain['vars'])
        state.apply(yaml_domain['constants'])
        vars = {}
        for _, t in yaml_domain['types'].items():
            vars.update({o: o for o in t})
        state.apply(vars)
        return state

    def test_run_tree(self):
        self.build_tree_example()

        state = self.get_state()

        res = self.pbt.tick(state)
        self.assertEqual(1, res.prob(lambda s: s['_S'] == 'F'))

        res = res.apply_delayed_actions()
        self.assertEqual(1, len(res.states))

        res.states[0][0]["grasped"] = "can"
        res.states[0][0]["close_to_object"]["can"] = "SUCCESS"

        res = self.pbt.tick(res)
        res = res.apply_delayed_actions()
        self.assertEqual(1, res.prob(lambda s: s['_S'] == 'F'))
        self.assertEqual(1, len(res.states))

        res.states[0][0]["location"] = "kitchen"
        #
        # print(self.pbt.nodes['__root_prec_0_cond'].func)
        # print(self.pbt.nodes['__root_prec_1_cond'].func)

        res = self.pbt.tick(res)
        res = res.apply_delayed_actions()

        self.assertEqual(0.9, res.prob(lambda s: s['has']['table2']['can'] == 'SUCCESS'))

    def test_verify(self):
        self.build_tree_example()
        state = self.get_state()

        state.states[0][0]["grasped"] = "can"
        state.states[0][0]["close_to_object"]["can"] = "SUCCESS"
        state.states[0][0]["location"] = "kitchen"

        res = self.pbt.verify(state)
        self.assertEqual(0.9, res.prob(lambda s: s['has']['table2']['can'] == 'SUCCESS'))

