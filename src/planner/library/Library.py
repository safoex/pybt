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


class TemplateLibrary:
    def __init__(self):
        self.templates = {}
        self.uuid = 0
        self.built = {}
        self.belief_memory = BeliefMemory({})
        self.memory = Memory()
        self.postconditions = {}
        self.vars = {}
        self.constants = {}

        self.planning_io = IO()
        self.planning_nodes = PlanningNodes(self.belief_memory)
        self.planning_import = Import(self.memory)
        self.planning_memories = Memories(self.memory)
        self.planning_templates = Templates(self.memory)
        self.planning_generic = GenericBuilder('builder', {'build'}, ['build', 'import', 'memory', 'templates', 'vars', 'nodes'])
        self.planning_io.reg(self.planning_nodes)
        self.planning_io.reg(self.planning_generic)
        self.planning_io.reg(self.planning_templates)
        self.planning_io.reg(self.planning_import)
        self.planning_io.reg(self.planning_memories)

        self.runtime_io = IO()
        self.runtime_nodes = Nodes(self.memory)
        self.running_import = Import(self.memory)
        self.running_memories = Memories(self.memory)
        self.runtime_templates = Templates(self.memory)
        self.runtime_generic = GenericBuilder('builder', {'build'}, ['build', 'import', 'memory', 'templates', 'vars', 'nodes'])
        self.runtime_io.reg(self.runtime_nodes)
        self.runtime_io.reg(self.runtime_templates)
        self.runtime_io.reg(self.runtime_generic)
        self.runtime_io.reg(self.running_memories)
        self.runtime_io.reg(self.running_import)

    def get_next_uuid(self, for_planning=True):
        if for_planning:
            _id = 'P' + str(self.uuid)
        else:
            _id = 'E' + str(self.uuid)
        self.uuid += 1
        return _id

    def get_yaml_def(self, _id, _type, args):
        yaml_def = {_id: {
            'type': _type,
            'root': True
        }}
        yaml_def[_id].update(args)

        return yaml_def

    def compile_node_for_runtime(self, _type, _args):
        """

        :param _type: type of template
        :param _args: args for template
        :return: return (id, nodes), whether nodes is a pyobj description
        """
        bt = BehaviorTree()
        self.runtime_io.reg(bt)
        _nodes = None

        def hook_function(task):
            nonlocal _nodes
            _nodes = task.message

        hook = Hook('hook', {'nodes_for_tree'}, hook_function)
        _id = self.get_next_uuid(for_planning=False)
        self.runtime_io.reg(hook)
        self.runtime_io.accept(Task({'nodes': self.get_yaml_def(_id, _type, _args)}, 'anon', keywords={'build'}))
        self.runtime_io.run_all()

        self.runtime_io.unreg(bt)
        self.runtime_io.unreg(hook)
        _nodes[_id].pop('root')
        return _id, {'nodes': _nodes}

    def load_templates(self, templates_file):
        task = Task(message=copy.deepcopy(templates_file), sender_name='anonymous', keywords={'build'})
        task2 = Task(message=templates_file, sender_name='anonymous', keywords={'build'})
        self.planning_io.accept(task)
        self.planning_io.run_all()

        self.runtime_io.accept(task2)
        self.runtime_io.run_all()

    def add_effect(self, var, val, prob, action):
        if var not in self.postconditions:
            self.postconditions[var] = {}
        if val not in self.postconditions[var]:
            self.postconditions[var][val] = []
        self.postconditions[var][val].append((prob, action))

    def load_domain(self, domain_file):
        domain = yaml.safe_load(domain_file)

        types = domain['types']
        for template, args in domain['actions'].items():
            args_domains = [[(k, t) for t in types[arg]] for k, arg in args.items()]
            for args_instance in itertools.product(*args_domains):
                d = {k: v for k, v in args_instance}
                d.update({'type': template})
                node = yaml.safe_dump(d)
                instance = self.planning_templates.compile_templated_node(node, "id")
                # print(instance)
                for postcondition in instance['nodes']['id']['postconditions']:
                    prob = postcondition['prob']
                    postcondition.pop('prob')
                    for var, val in postcondition.items():
                        self.add_effect(var, val, prob, (template, d))

        self.vars = domain['vars']
        self.constants = domain['constants']
        for _, ol in types.items():
            for o in ol:
                self.constants[o] = o

    def compile_bt_for_planning_from_nodes(self, nodes):
        bt = PlanningBehaviorTree()
        self.planning_io.reg(bt)
        self.planning_io.accept(Task(nodes, 'anon', keywords={'build'}))
        self.planning_io.run_all()
        self.planning_io.unreg(bt)
        return bt

    def compile_node_for_planning(self, _id, _type, _args):
        if id is None:
            _id = self.get_next_uuid(for_planning=True)
        yaml_def = self.get_yaml_def(_id, _type, _args)
        return self.compile_bt_for_planning_from_nodes({'nodes': yaml_def}).root

    def build_and_save_template_with_args(self, _type, _args, _id=None):
        if id is None:
            _id = self.get_next_uuid(for_planning=True)
        self.templates[self.get_yaml_def(_id, _type, _args)] = (
        self.compile_node_for_planning(_id, _type, _args), _type, _args)

    def bucketize_from(self, initial_state, subset_of_templates=None):
        return [(tbt.tick(with_memory=copy.deepcopy(initial_state)), t_type, t_args) for tbt, t_type, t_args in
                subset_of_templates or self.templates]

    def get_all_nonzero_prob(self, initial_state, with_bt):
        bucketized = self.bucketize_from(initial_state)
        bucketized = [(bucket, t, a) for bucket, t, a in bucketized if 'S' in dict(bucket)]
        bucketized = [(with_bt.tick(with_memory=dict(bucket)['S']), t, a) for bucket, t, a in bucketized]
        bucketized = [(bucket, t, a, bucket['S'].prob()) for bucket, t, a in bucketized if 'S' in dict(bucket)]
        bucketized.sort(key=lambda x: x[3])

        to_return = [(self.compile_node_for_runtime(t, a), t, a) for bucket, t, a, p in bucketized]
        to_return = [(_id, self.compile_node_for_planning(_id, t, a), nodes) for _id, nodes, t, a in to_return]
        # (id, planning_node_root, yaml_nodes_def)
        return to_return

    def get_candidate_actions(self, condition, history, state):
        candidates = []
        val = condition['val']
        for pvar, pvals in self.postconditions.items():
            for pval, possible_actions in pvals.items():
                for (prob, (template, args)) in possible_actions:
                    # TRICK!
                    var = copy.deepcopy(condition['var'])
                    if pval is None:
                        pval = 'None'
                    var = var.replace(pvar, pval)
                    state.exec({
                        'S': var + ' == ' + val
                    })
                    prob_on_state = state.prob({state.state_key: 'S'})
                    if prob_on_state > 0:
                        candidates.append((prob_on_state * prob, (template, args)))
        candidates.sort(key=lambda c: c[0])
        return [(t, a) for c, (t, a) in candidates]

    def get_best_templates_for_condition(self, condition: dict, history, state: BeliefMemory):
        """
        finds suitable actions to resolve (pre)condition.

        :param condition: goal condition (need to be satisfied)
        :param history: ???
        :param state: current belief state
        :return: [(compiled_planning_node, runtime_id, runtime_nodes_definition)]
        """
        if 'var' not in condition and 'val' not in condition:
            return []
        condition = copy.deepcopy(condition)
        for k in condition:
            condition[k] = Memory.unquote(condition[k])
        print(condition)
        candidates = self.get_candidate_actions(condition, history, state)
        return [
            (
                self.compile_node_for_planning(self.get_next_uuid(for_planning=True), t, a),
                *self.compile_node_for_runtime(t, a)
            ) for t, a in candidates]

    def check_if_action_threats_condition(self, action, _condition):
        """

        :param action:
        :param condition:
        :return:
        """
        # TODO: rewrite
        condition = copy.deepcopy(_condition)
        ctx = copy.deepcopy(self.vars)
        ctx.update({condition['var']: condition['val']})
        if isinstance(action, dict):
            action = sum([k + ' = ' + v + '\n' for k, v in action.items()])
        exec(action, ctx)
        return not eval(condition['var'] + ' == ' + condition['val'], ctx)

    def check_if_action_sets_condition(self, action, _condition):
        condition = copy.deepcopy(_condition)

        for a_var, a_val in action:
            condition['var'] = condition['var'].replace(a_var, a_val)

        cnts = copy.deepcopy(self.constants)
        return eval(condition['var'] + ' == ' + condition['val'], cnts)
