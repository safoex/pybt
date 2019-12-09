from ruamel import yaml
import src.core.nodes.sequential as sequential
import src.core.nodes.leaf as leaf


class Nodes(object):
    def __init__(self, memory):
        self.memory = memory

    @staticmethod
    def _check_and_raise(node, params, appendix=""):
        if not isinstance(params, list):
            params = [params]
        for p in params:
            if p not in node:
                raise RuntimeWarning("missing " + p + appendix)

    def build_from_yaml(self, yml, id=None):
        """
        build python node from yaml representation for Action, Condition or Sequential classes.
        Note, that for Sequential .children list will be empty.
        Further processing fills .children with other nodes (objects, not just ids!).
        :param yml: string with yaml description of a node. Dictionary
        :param id: you can provide an id explicitly or modify the one from yaml dictionary
        :return: Action, Condition or Sequential node
        """
        node = yaml.safe_load(yml)
        return self.build_from_python(node, id)
    
    def build_from_python(self, node, id=None):
        """
        build python node from yaml representation for Action, Condition or Sequential classes.
        Further processing replace names in .children with other nodes (objects, not just ids!).
        :param node: python dict with a description of a node. Dictionary
        :param id: you can provide an id explicitly or modify the one from python dictionary
        :return: Action, Condition or Sequential node
        """
        if id is None:
            self._check_and_raise(node, 'id')
            id = node['id']
        self._check_and_raise(node, 'type', 'for node '+id)
        type = node['type']
        if type == 'action':
            self._check_and_raise(node, 'script', 'for node '+id)
            return leaf.Action(name=id, memory=self.memory, expression=node['script'])
        elif type == 'condition':
            params = ['expression', 'true_state', 'false_state']
            self._check_and_raise(node, params, 'for node ' + id)
            return leaf.Condition(name=id, memory=self.memory, **dict((k, node[k]) for k in params))
        elif type in ['sequence', 'fallback', 'skipper']:
            seq = sequential.Sequential(return_state=sequential.Sequential.Names[type], name=id, memory=self.memory)
            self._check_and_raise(node, 'children', 'for node ' + id)
            seq.children = node['children']

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
            for type in sequential.Sequential.Names:
                if sequential.Sequential.Names[type] == obj.return_state:
                    pydict['type'] = type
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
        for i, child in enumerate(descriptions[node_name].children):
            new_node = self.build_from_python(descriptions[child], child)
            new_node.children = []
            bt.execute({child, [node_name, i, new_node]})
            self.req_add_children(descriptions, bt, child)

    def build_collection(self, descriptions, bt, root_name=None):
        if isinstance(descriptions, str):
            descriptions = yaml.safe_load(descriptions)
        elif isinstance(descriptions, list):
            descriptions = {o.id: o for o in descriptions}

        if bt.root_name is None and root_name is None:
            raise RuntimeWarning('no root specified for .build_collection')
        elif bt.root_name is None:
            bt.root_name = root_name

        bt.nodes[bt.root_name] = self.build_from_python(descriptions[bt.root_name], bt.root_name)
        self.req_add_children(descriptions, bt, bt.root_name)
