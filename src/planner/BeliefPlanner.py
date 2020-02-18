from src.planner.belief_memory.belief_memory import BeliefMemory
from src.planner.PlanningBehaviorTree import PlanningBehaviorTree
from src.planner.nodes.planning_node import PlanningSequential, PlanningLeaf
from ruamel import yaml
from src.planner.library.Library import TemplateLibrary
from src.core.build.yaml.templates import Templates
import functools
import copy


class BeliefPlanner:
    def __init__(self, partial_behavior_tree, library: TemplateLibrary,
                 ticks_limit=100, states_limit=100):
        self.bt_def = None
        if isinstance(partial_behavior_tree, str):
            partial_behavior_tree = yaml.safe_load(partial_behavior_tree)
        self.bt_def = partial_behavior_tree
        self.library = library
        self.pbt = self.library.compile_bt_for_planning_from_nodes(self.bt_def)
        self.ticks_limit = ticks_limit
        self.states_limit = states_limit
        self.permutation_graph = {}

    def rearrange_children(self, parent: str, new_order: [str], bt: PlanningBehaviorTree = None):
        if bt is None:
            bt = self.pbt
        remap = {
            name: i for i, name in enumerate(new_order)
        }
        self.bt_def['nodes'][parent]['children'] = new_order

        old_children = bt.nodes[parent].children
        bt.nodes[parent].children = [
            old_children[remap[c.id]] for c in old_children
        ]

    def swap_children(self, child1: str, child2: str, parent: str, bt: PlanningBehaviorTree):
        new_order = []
        for c in bt.nodes[parent]:
            if c.id != child1 and c.id != child2:
                new_order.append(c.id)
            else:
                if c.id == child1:
                    new_order.append(child2)
                else:
                    new_order.append(child1)
        self.rearrange_children(parent, new_order, bt)

    def insert_actions(self, parent: str, actions: list, bt: PlanningBehaviorTree):
        children_already = len(bt.nodes[parent].children)
        planning_bt_query = [(parent, i + children_already, action) for i, (action, _id, _rt_nodes) in
                             enumerate(actions)]
        rt_nodes_query = [_rt_nodes for _, _, _rt_nodes in actions]
        self.bt_def['nodes'][parent]['children'] = self.bt_def['nodes'][parent]['children'] + [_id for _, _id, _ in actions]
        self.bt_def = functools.reduce(Templates.merger.merge, rt_nodes_query, self.bt_def)
        bt.execute({
            PlanningBehaviorTree.INSERT: planning_bt_query
        })

    def resolve_precondition_with_inserting_actions(self, precondition: str, initial_state: BeliefMemory):
        actions = self.library.get_best_templates_for_condition(precondition, None, initial_state)
        parent = self.get_parent(precondition)
        if parent is None:
            raise RuntimeWarning("something went wrong - no parent found for node " + precondition)
        self.insert_actions(parent, actions)

    def get_parent(self, node_name: str):
        for k, node_def in self.bt_def['nodes']:
            if 'children' in node_def and node_name in node_def['children']:
                return k
        return None

    @staticmethod
    def _set_self_state(node, buckets):
        for s, p in buckets.states:
            s[node.id] = s[buckets.state_key]

    def find_lowest_failed_condition(self, status: str, ps: dict, bt: PlanningBehaviorTree):
        conditions = {}
        for name, node in bt.nodes.items():
            if isinstance(node, PlanningLeaf) and 'var' in node.func:
                conditions[name] = None
        height = 0
        current = [bt.root]
        nexts = []
        while len(current) != 0:
            for left, node in enumerate(current):
                if node.id in conditions and node.id in ps and ps[node.id] == status:
                    conditions[node.id] = (height, left)
                nexts += node.children
            height += 1
            current, nexts = nexts, current
            nexts.clear()
        conditions_array = [(*x, name) for name, x in conditions.items() if x is not None]
        conditions_array.sort()
        return conditions_array[-1] if len(conditions_array) > 0 else None

    def find_most_popular_failed_condition(self, status: str, mem: BeliefMemory, bt: PlanningBehaviorTree):
        # deepest :status: condition?
        conditions = {}
        for ps, pr in mem.states:
            res = self.find_lowest_failed_condition(status, ps, bt)
            if res is not None:
                h, l, name = res
                if name in conditions:
                    conditions[name] += BeliefMemory(ps, pr)
                else:
                    conditions[name] = BeliefMemory(ps, pr)
        results = list(reversed(sorted([(occs.prob(), name) for name, occs in conditions.items()])))
        print(results)
        if len(results) > 0:
            cond =  results[0][1]
            return conditions[cond], cond
        else:
            return None

    def find_next_condition_to_resolve(self, initial_state: BeliefMemory, bt: PlanningBehaviorTree):
        for name, node in bt.nodes.items():
            if isinstance(node, PlanningLeaf) and 'var' in node.func:
                node._after_tick = BeliefPlanner._set_self_state

        mem = copy.deepcopy(initial_state)
        mem = bt.tick(mem)
        stopped = {
            state: self.find_most_popular_failed_condition(state, mem, bt)
            for state in ['R', 'F']
        }
        if stopped['R'] is None:
            more_popular_state = 'F'
        elif stopped['F'] is None:
            more_popular_state = 'R'
        else:
            more_popular_state = 'R' if stopped['R'][0].prob() > stopped['F'][0].prob() else 'F'

        condition_to_resolve = stopped[more_popular_state][1]

        for name, node in bt.nodes.items():
            node._after_tick = None
        return condition_to_resolve, more_popular_state, stopped[more_popular_state][0]

    def find_threats(self, cond_name: str, state: BeliefMemory, bt: PlanningBehaviorTree):
        condition = bt.nodes[cond_name].func
        for ps in state.states:
            if state.action_history_key in ps:
                threat = None
                for a_id, action in reversed(ps[state.action_history_key]):
                    if self.library.check_if_action_sets_condition(action, condition):
                        break
                    if self.library.check_if_action_threats_condition(action, condition):
                        threat = a_id
                        break
                if threat is not None:
                    return threat
        return None

    def resolve_threat(self, target_condition: str, threat, bt: PlanningBehaviorTree):

        ncr = bt.find_ncr(target_condition, threat)
        if ncr == bt.root.id:
            raise RuntimeError("IMPOSSIBLE TO RESOLVE THREATS: " + str(threat) + "WHICH THREATS " + target_condition)

        # I bet it should be preconditions. If not, let's raise another error!

        threat_path = bt.path_from_root(threat)
        next_to_threat = threat_path.index(ncr) + 1
        target_condition_path = bt.path_from_root(target_condition)
        next_to_target = target_condition_path.index(ncr) + 1

        children = [copy.copy(c.id) for c in bt.nodes[ncr].children]

        children.remove(next_to_target)
        children.insert(children.index(next_to_threat), next_to_target)
        self.rearrange_children(ncr, children, bt)

    def resolve_open_goal(self, target_condition: str, state: BeliefMemory, bt: PlanningBehaviorTree):
        parent = bt.find_parent(target_condition)
        if bt.nodes[parent].skip_state == PlanningSequential.Sequence:
            parent = bt.find_parent(parent)
        best_actions = self.library.get_best_templates_for_condition(bt.nodes[target_condition].func, None, state)
        self.insert_actions(parent, [best_actions[0]], bt)

    def resolve_one_issue(self, initial_state: BeliefMemory, bt: PlanningBehaviorTree):
        next_condition = self.find_next_condition_to_resolve(initial_state, bt)
        if next_condition is None:
            return 0
        target, status, substate = next_condition
        print(target)
        threat = self.find_threats(target, substate, bt)
        insert_operations = 0
        if threat is not None:
            self.resolve_threat(target, threat, bt)
        else:
            self.resolve_open_goal(target, substate, bt)
            insert_operations = 1
        return insert_operations

    def refine_to(self, initial_state, bt: PlanningBehaviorTree, goal_probability=0.9):
        result = bt.verify(initial_state, ticks_limit=self.ticks_limit, states_limit=self.states_limit)
        finished, to_refine = result.split_by(lambda s: s[result.state_key] == 'S')
        new_goal = goal_probability - finished.prob()
        if new_goal > 0:
            pass
        else:
            return

    def refine_till(self, initial_state: BeliefMemory, bt: PlanningBehaviorTree, goal_probability=0.9, nodes_max=100):
        total_inserted = 0
        last_prob = 0
        to_refine = copy.deepcopy(initial_state)
        while total_inserted < nodes_max and last_prob < goal_probability:
            total_inserted += self.resolve_one_issue(to_refine, bt)
            result = bt.verify(copy.deepcopy(initial_state), ticks_limit=self.ticks_limit,
                               states_limit=self.states_limit)
            finished, to_refine = result.split_by(lambda s: s[result.state_key] == 'S')
            last_prob = finished.prob()
            for s, p in to_refine.states:
                print(s['_S'], p)
        return last_prob, total_inserted
