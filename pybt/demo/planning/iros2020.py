from pybt.src.planner.build.planning_nodes import PlanningNodes
from pybt.src.core.build.yaml.templates import Templates
from pybt.src.core.build.yaml.memories import Memories
from pybt.src.core.build.yaml.generic import GenericBuilder
from pybt.src.core.memory.memory import Memory
from pybt.src.core.build.yaml.imports import Import
from pybt.src.core.io.io import Task, IO
from ruamel import yaml
from pybt.src.planner.PlanningBehaviorTree import PlanningBehaviorTree
from pybt.src.planner.library.Library import TemplateLibrary
from pybt.src.planner.BeliefPlanner import BeliefPlanner
import copy
from pybt.src.planner.belief_memory.belief_memory import BeliefMemory
from pybt.src.ui.abtm_bridge import ABTMAppChannel
import threading
import pickle
from definitions import ROOT_DIR

class Demo:
    def __init__(self):
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
        with open(ROOT_DIR + "/demo/planning/domain.yaml") as df:
            self.domain = df.read()
        with open(ROOT_DIR + "/demo/planning/templates.yaml") as tf:
            self.templates = tf.read()

        self.examples = [
            """
            nodes:
                root:
                    type: t/seen
                    root: yes
                    what: soda
                    post_check_condition: null
            """,
            """
            nodes:
                root:
                    type: t/nowhere
                    root: yes
                    object: dirt
            """

        ]

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
        with open(ROOT_DIR + "/demo/planning/templates.yaml") as tf:
            self.load_templates(tf.read())
        self.nodes = nodes
        self.build_tree(self.nodes)

    def build_tree_example(self, num):
        assert num in (0, 1)
        self.build_tree_with(self.examples[num])

    def get_state(self):
        with open(ROOT_DIR + "/demo/planning/domain.yaml") as df:
            yaml_domain = yaml.safe_load(df)
        state = BeliefMemory(yaml_domain['vars'])
        state.apply(yaml_domain['constants'])
        vars = {}
        for _, t in yaml_domain['types'].items():
            vars.update({o: o for o in t})
        state.apply(vars)
        return state

    def get_physical_state(self):
        with open(ROOT_DIR + "/demo/planning/domain.yaml") as df:
            yaml_domain = yaml.safe_load(df)
        mem = Memory()
        mem.vars.update(yaml_domain['vars'])
        mem.vars.update(yaml_domain['constants'])
        for _, t in yaml_domain['types'].items():
            mem.vars.update({o: o for o in t})
        return mem

    def visualize(self):
        self.viewer = ABTMAppChannel()
        self.io = IO()
        self.io.reg(self.viewer)
        self.viewer_thread = threading.Thread(target=lambda: self.viewer.run())
        self.viewer_thread.start()
        self.io.accept(Task(message=self.bpl.bt_def['nodes'], sender_name='anon', keywords={'nodes_for_tree'}))
        self.io.run_all()

    def test_example(self, example: int = 1, prob=0.93, nodes_limit=30):
        self.build_tree_example(int(example))
        self.load_lib()
        self.bpl = BeliefPlanner(self.nodes, self.lib)
        initial_state = self.get_state()
        # try:
        ref_res = self.bpl.refine_till(initial_state, self.pbt, prob, nodes_max=nodes_limit)
        res = self.pbt.verify(initial_state)

        pickle.dump(self.bpl.bt_def, open('saved_nodes_nowhere.nds', 'wb'))
        # except BaseException:
        #     pass
        # yaml.dump(self.bpl.bt_def, open('saved_nodes_find.yaml', 'w'))
        self.visualize()
