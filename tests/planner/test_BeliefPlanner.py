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
from src.planner.BeliefPlanner import BeliefPlanner
from src.planner.library.Library import TemplateLibrary
import copy
from src.planner.belief_memory.belief_memory import BeliefMemory


class TestBeliefPlanner(TestCase):
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

        self.lib = TemplateLibrary()
        with open("build/yaml/domain.yaml") as df:
            self.domain = df.read()
        with open("build/yaml/templates.yaml") as tf:
            self.templates = tf.read()

    def load_lib(self):
        self.lib.load_templates(self.templates)
        self.lib.load_domain(self.domain)

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
        self.nodes = """
        nodes:
            root:
                type: t/put
                root: yes
                object: can
                place: table2
        """
        self.build_tree(self.nodes)

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

    def test_one_issue(self):
        self.build_tree_example()
        self.load_lib()
        self.bpl = BeliefPlanner(self.nodes, self.lib)
        initial_state = self.get_state()
        initial_state = self.pbt.tick(initial_state)
        # print(initial_state)
        print(self.bpl.resolve_one_issue(initial_state, self.pbt))
