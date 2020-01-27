from ruamel import yaml
import src.core.nodes.sequential as sequential
import src.core.nodes.leaf as leaf
import src.core.tree.behavior_tree as behavior_tree
import copy
from definitions import State
from src.core.build.yaml.generic import GenericBuilder
from src.core.io.io import Task


class Nodes(GenericBuilder):
    def __init__(self, memory):
        super().__init__('nodes', {'nodes'})
        self.memory = memory

    @staticmethod
    def _check_and_raise(node, params, appendix=""):
        if not isinstance(params, list):
            params = [params]
        for p in params:
            if p not in node or node[p] is None:
                raise RuntimeWarning("missing " + p + appendix)

    def build_from_yaml(self, yml, _id=None):
        """
        build python node from yaml representation for Action, Condition or Sequential classes.
        Note, that for Sequential .children list will be empty.
        Further processing fills .children with other nodes (objects, not just ids!).
        :param yml: string with yaml description of a node. Dictionary
        :param _id: you can provide an id explicitly or modify the one from yaml dictionary
        :return: Action, Condition or Sequential node
        """
        node = yaml.safe_load(yml)
        return self.build_from_python(node, _id)

    def build_action_from_python(self, node, _id):
        self._check_and_raise(node, 'script', ' for node ' + _id)
        return leaf.Action(name=_id, memory=self.memory, expression=node['script'])

    def build_condition_from_python(self, node, _id):
        params = ['expression', 'true_state', 'false_state']
        self._check_and_raise(node, params, ' for node ' + _id)
        node_copy = copy.copy(node)
        for state in ['true_state', 'false_state']:
            if isinstance(node[state], str):
                node_copy[state] = State.from_str(node[state])
        return leaf.Condition(name=_id, memory=self.memory, **dict((k, node_copy[k]) for k in params))

    def build_sequential_from_python(self, node, _id, _type):
        seq = sequential.Sequential(skip_state=sequential.Sequential.Names[_type], name=_id, memory=self.memory)
        self._check_and_raise(node, 'children', ' for node ' + _id)
        seq.children = node['children']
        return seq

    def build_from_python(self, node, _id=None):
        """
        build python node from yaml representation for Action, Condition or Sequential classes.
        Further processing replace names in .children with other nodes (objects, not just ids!).
        :param node: python dict with a description of a node. Dictionary
        :param _id: you can provide an id explicitly or modify the one from python dictionary
        :return: Action, Condition or Sequential node
        """
        if _id is None:
            self._check_and_raise(node, 'id')
            _id = node['id']
        self._check_and_raise(node, 'type', ' for node ' + _id)
        _type = copy.copy(node['type'])
        if _type == 'action':
            return self.build_action_from_python(node, _id)
        elif _type == 'condition':
            return self.build_condition_from_python(node, _id)
        elif _type in ['sequence', 'fallback', 'skipper', 'selector']:
            if _type == 'selector':
                _type = 'fallback'
            return self.build_sequential_from_python(node, _id, _type)

    @staticmethod
    def dump_to_python(obj):
        """
        dump python dict representation of Behavior Tree primary node (Action, Condition or Sequential).
        :param obj: python instance of aforementioned classes
        :return: dict with description of this node
        """
        pydict = {}
        if not isinstance(obj, leaf.Action) and not isinstance(obj, leaf.Condition) \
                and not isinstance(obj, sequential.Sequential):
            raise RuntimeWarning("You can dump only following classes: Action, Condition, Sequential")
        pydict['id'] = obj.id
        if isinstance(obj, leaf.Action):
            pydict['type'] = 'action'
            pydict['script'] = obj.expression
        if isinstance(obj, leaf.Condition):
            pydict['type'] = 'condition'
            pydict['expression'] = obj.expression
            pydict['true_state'] = obj.true_state
            pydict['false_state'] = obj.false_state
        if isinstance(obj, sequential.Sequential):
            for _type in sequential.Sequential.Names:
                if sequential.Sequential.Names[_type] == obj.skip_state:
                    pydict['type'] = _type
            pydict['children'] = [child.id for child in obj.children]
        return pydict

    def dump_to_yaml(self, obj):
        """
        dump yaml representation of Behavior Tree primary node (Action, Condition or Sequential).
        :param obj: python instance of aforementioned classes
        :return: yaml string with description of this node
        """
        pydict = self.dump_to_python(obj)
        return yaml.safe_dump(pydict)

    def req_add_children(self, descriptions, bt, node_name):
        if 'children' in descriptions[node_name]:
            for i, child in enumerate(descriptions[node_name]['children']):
                new_node = self.build_from_python(descriptions[child], child)
                new_node.children = []
                bt.execute({bt.INSERT: [(node_name, i, new_node)]})
                self.req_add_children(descriptions, bt, child)

    def build_collection(self, descriptions, root_name):
        if isinstance(descriptions, str):
            descriptions = yaml.safe_load(descriptions)
        elif isinstance(descriptions, list):
            descriptions = {o.id: o for o in descriptions}

        root = self.build_from_python(descriptions[root_name], root_name)
        root.children = []
        bt = behavior_tree.BehaviorTree(memory=self.memory, root_node=root)

        self.req_add_children(descriptions, bt, root_name)
        return bt

    def on_message(self, task):
        nodes = task.message
        if isinstance(task.message, str):
            nodes = yaml.safe_load(task.message)
        if not isinstance(nodes, dict):
            raise RuntimeWarning('nodes could be loaded only from dict or yaml string')

        # check if there are any not built templated node:
        for node_name, node_def in nodes.items():
            if 'type' in node_def and node_def['type'][:2] == 't/':
                return Task(nodes, self.name, {'templated_nodes', 'node'}, priority=task.priority)

        # find root:
        root_name = None
        for node_name, node_def in nodes.items():
            if 'root' in node_def:
                root_name = node_name
        if root_name is None:
            raise RuntimeWarning("Some node should be a root. (hint: add root field to node definition!)")

        # build collection:
        bt = self.build_collection(nodes, root_name)

        return [Task(bt, self.name, {'behavior_tree', 'new'}), Task(nodes, self.name, {'nodes_for_tree'})]
