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
from src.ui.abtm_bridge import ABTMAppChannel
import threading
import time


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

    def build_tree_with(self, nodes):
        with open("build/yaml/templates.yaml") as tf:
            self.load_templates(tf.read())
        self.nodes = nodes
        self.build_tree(self.nodes)

    def build_tree_example(self):
        nodes = """
        nodes:
            root:
                type: t/put
                root: yes
                object: can
                place: table2
                post_check_condition: null
        """
        self.build_tree_with(nodes)

    def build_tree_example2(self):
        nodes = """
        nodes:
            root:
                type: t/grasp
                root: yes
                object: bottle
                post_check_condition: null
        """
        self.build_tree_with(nodes)


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

    def visualize(self):
        self.viewer = ABTMAppChannel()
        self.io = IO()
        self.io.reg(self.viewer)
        self.viewer_thread = threading.Thread(target=lambda: self.viewer.run())
        self.viewer_thread.start()
        self.io.accept(Task(message=self.bpl.bt_def['nodes'], sender_name='anon', keywords={'nodes_for_tree'}))
        self.io.run_all()

    # def test_one_issue(self):
    #     self.build_tree_example()
    #     self.load_lib()
    #     self.bpl = BeliefPlanner(self.nodes, self.lib)
    #     initial_state = self.get_state()
    #     initial_state = self.pbt.tick(initial_state)
    #     # print(initial_state)
    #     self.bpl.resolve_one_issue(initial_state, self.pbt)
    #     initial_state.states[0][0]["close_to_object"]["can"] = "SUCCESS"
    #     initial_state.states[0][0]["has"]["table2"]["can"] = "FAILURE"
    #     initial_state.states[0][0]["location"] = "kitchen"
    #     initial_state.states[0][0]["grasped"] = None
    #     res = self.pbt.verify(initial_state)
    #     # self.visualize()
    #     self.assertEqual(0.8*0.9, res.prob(lambda s: s['has']['table2']['can'] == "SUCCESS"))
    #
    # def test_simple_goal(self):
    #     self.build_tree_example()
    #     self.load_lib()
    #     self.bpl = BeliefPlanner(self.nodes, self.lib)
    #     initial_state = self.get_state()
    #     initial_state.states[0][0]["close_to_object"]["can"] = "SUCCESS"
    #     initial_state.states[0][0]["has"]["table2"]["can"] = "FAILURE"
    #     initial_state.states[0][0]["location"] = "kitchen"
    #     initial_state.states[0][0]["grasped"] = None
    #     self.bpl.refine_till(initial_state, self.pbt, 0.7)
    #
    #     res = self.pbt.verify(initial_state)
    #     # for s, p in res.states:
    #     #     print(s['_S'], p)
    #     self.assertEqual(0.8*0.9, res.prob(lambda s: s['has']['table2']['can'] == "SUCCESS"))
    #
    # def test_two_step_goal(self):
    #     self.build_tree_example()
    #     self.load_lib()
    #     self.bpl = BeliefPlanner(self.nodes, self.lib)
    #     initial_state = self.get_state()
    #     initial_state.states[0][0]["close_to_object"]["can"] = "SUCCESS"
    #     initial_state.states[0][0]["seen"]["can"] = "SUCCESS"
    #     initial_state.states[0][0]["has"]["table2"]["can"] = "FAILURE"
    #     initial_state.states[0][0]["location"] = "postdocroom"
    #     initial_state.states[0][0]["grasped"] = None
    #     self.bpl.refine_till(initial_state, self.pbt, 0.7)
    #     res = self.pbt.verify(initial_state)
    #     for s, p in res.states:
    #         print(s['_S'], p)
    #     # self.visualize()

    def test_three_step_goal(self, prob=0.75, nodes_limit=20):
        self.build_tree_example()
        self.load_lib()
        self.bpl = BeliefPlanner(self.nodes, self.lib)
        initial_state = self.get_state()
        initial_state.states[0][0]["close_to_object"]["can"] = "SUCCESS"
        initial_state.states[0][0]["seen"]["can"] = "SUCCESS"
        initial_state.states[0][0]["has"]["table2"]["can"] = "FAILURE"
        initial_state.states[0][0]["location"] = "postdocroom"
        initial_state.states[0][0]["grasped"] = None
        ref_res = self.bpl.refine_till(initial_state, self.pbt, prob, nodes_max=nodes_limit)
        res = self.pbt.verify(initial_state)
        for s, p in res.states:
            print(s['_S'], p)
        print(ref_res)
        # self.visualize()

    def test_big_goal(self, prob=0.9, nodes_limit=20):
        self.build_tree_example()
        self.load_lib()
        self.bpl = BeliefPlanner(self.nodes, self.lib)
        initial_state = self.get_state()
        ref_res = self.bpl.refine_till(initial_state, self.pbt, prob, nodes_max=nodes_limit)

        res = self.pbt.verify(initial_state)
        for s, p in res.states:
            print(s['_S'], p)
        print(ref_res)
        self.visualize()


from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import cProfile, pstats, io


def make_call_graph():
    test = TestBeliefPlanner()
    test.setUp()

    with PyCallGraph(output=GraphvizOutput()):
        test.test_three_step_goal()

def measure_times():
    pr = cProfile.Profile()
    test = TestBeliefPlanner()
    test.setUp()

    pr.enable()
    test.test_three_step_goal(prob=0.995)

    # ... do something ...
    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


if __name__ == "__main__":
    measure_times()