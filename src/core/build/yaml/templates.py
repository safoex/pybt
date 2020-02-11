from src.core.build.yaml.nodes import Nodes
from src.core.io.io import Task
import copy
import deepmerge
import functools


class Templates(Nodes):
    merger = deepmerge.Merger(
        [(dict, ["merge"])],
        ['override'],
        ['override']
    )

    ANY = "AANNYY"

    def __init__(self, memory):
        super().__init__(memory)
        self.name = 'templates'
        self.keywords = {'nodes', 'templates', 'templated_nodes'}
        self.templates = dict()

    def load_template(self, template_yaml, name=None):
        """
        loads a yaml description of the template to memory
        :param template_yaml: yaml description of the template
        :param name: name of template
        :return: None
        """
        template = self.yaml.load(template_yaml)

        if name is None:
            self._check_and_raise(template, 'name', 'in a template')
            name = template['name']

        self.templates[name] = template_yaml

    @staticmethod
    def any_arg_in_string(args, s):
        args = ['$' + k if k[0] != '$' else k for k in args.keys()]
        for a in args:
            if a in s:
                return True
        return False

    @staticmethod
    def cyclicly_replace_args_in_text(replacements, text):
        while Templates.any_arg_in_string(replacements, text):
            for arg_name in replacements:
                if arg_name in text:
                    text = text.replace(arg_name, str(replacements[arg_name]))
        return text

    @staticmethod
    def get_all_argument_names(args_py):
        args = []
        has_optional = 'optional' in args_py
        has_required = 'required' in args_py

        if has_required:
            for arg_name in args_py['required']:
                args.append(arg_name)

        if has_optional:
            for arg_name in args_py['optional'].keys():
                args.append(arg_name)

        return args

    @staticmethod
    def get_optional_and_required_arguments(args_py, node_py):
        reps = dict()

        reps['$name'] = node_py['id']

        has_optional = 'optional' in args_py
        has_required = 'required' in args_py

        if has_required:
            for arg_name in args_py['required']:
                Nodes._check_and_raise(node_py, arg_name)
                reps['$' + arg_name] = node_py[arg_name]

        if has_optional:
            for arg_name in args_py['optional'].keys():
                if arg_name in node_py:
                    reps['$' + arg_name] = node_py[arg_name]
                else:
                    reps['$' + arg_name] = args_py['optional'][arg_name]

        return reps

    def get_args_without_self_dependenices(self, args_py, node_py):
        replacements = Templates.get_optional_and_required_arguments(args_py, node_py)

        args_text = self.yaml.dump(args_py)
        args_text = Templates.cyclicly_replace_args_in_text(replacements, args_text)
        return self.yaml.load(args_text)

    @staticmethod
    def replace_from(source, rep_table=None):
        result = ""

        if rep_table is None:
            rep_table = dict()

        if isinstance(rep_table, dict):
            V = rep_table['V'] if 'V' in rep_table else '$V'
            K = rep_table['K'] if 'K' in rep_table else '$K'
            rep_table = [(K, V) for i, _ in enumerate(source)]

        if isinstance(source, list):
            result = []
            for (k, old_value), (rep_K, rep_V) in zip(enumerate(source), rep_table):
                new_value = copy.copy(rep_V)
                new_value = Templates.cyclicly_replace_args_in_text({'$V': old_value, '$K': str(k)}, new_value)
                result.append(new_value)
        elif isinstance(source, dict):
            result = {}
            for (old_key, old_value), (rep_V, rep_K) in zip(source.items(), rep_table):
                new_value = copy.copy(rep_V)
                new_key = copy.copy(rep_K)
                reps = {'$V': old_value, '$K': old_key}
                new_value = Templates.cyclicly_replace_args_in_text(reps, new_value)
                new_key = Templates.cyclicly_replace_args_in_text(reps, new_key)
                result[new_key] = new_value
        else:
            result = source

        return result

    @staticmethod
    def add_construct_replacements(replacements, args_py):
        has_construct = 'construct' in args_py

        if has_construct:
            for arg_name in args_py['construct'].keys():
                arg_def = args_py['construct'][arg_name]
                Templates._check_and_raise(arg_def, 'from', 'in construct for ' + arg_name)
                arg_name_from = arg_def['from']
                Templates._check_and_raise(replacements, '$' + arg_name_from, ' as a source for constructing ' + arg_name)
                source = replacements['$' + arg_name_from]

                replacements['$' + arg_name] = Templates.replace_from(source, arg_def)

        return replacements

    def unpack_requirsevily(self, template_py, replacements):
        while 'unpack' in template_py and isinstance(template_py['unpack'], dict):
            unpacked = []
            for arg_name, to_unpack in template_py['unpack'].items():
                unpacked_arg_name = Templates.replace_from(
                    replacements['$' + arg_name],
                    {'V': self.yaml.dump(to_unpack)}
                )
                for piece in unpacked_arg_name:
                    unpacked.append(self.yaml.load(piece))
            template_py.pop('unpack')
            template_py = functools.reduce(Templates.merger.merge, unpacked, template_py)
        return template_py

    def compile_pre_and_post_conditions(self, type_, args, lazy=False):
        self._check_and_raise(self.templates, type_, ' in saved templates')

        template = copy.copy(self.templates[type_])
        # template = template.replace('~', '_$name_')
        template_py = self.yaml.load(template)

        self._check_and_raise(template_py, 'args', 'in template ' + type_)

        for arg in self.get_all_argument_names(template_py['args']):
            if arg not in args:
                args[arg] = Templates.ANY

        replacements = self.get_optional_and_required_arguments(
            self.get_args_without_self_dependenices(template_py['args'], args), args)

        keys_for_planner = ['preconditions', 'postconditions']
        template_py_for_planner = {k: v for k, v in template_py.items() if k in keys_for_planner}

        template_text_for_planner = Templates.cyclicly_replace_args_in_text(replacements,
                                                                            self.yaml.dump(template_py_for_planner))

        return self.yaml.load(template_text_for_planner)

    def apply_build_script(self, function_code, args, template_py):
        return Templates.merger.merge(template_py, self.memory.exec_function_with_return(function_code, args))

    def delayed_compile_templated_node(self, template_py, args):
        pass

    def compile_templated_node(self, node_description_yaml, id_=None, lazy=False):
        """
        create a collection of nodes and variable declarations out of node_description
        :param node_description_yaml: yaml dict with description of templated node
        :param id_: id of node
        :return: a collection of nodes and variables (python dict {'nodes': {...}, 'vars': {...}})
        """
        node = self.yaml.load(node_description_yaml)

        if 'id' not in node:
            node['id'] = id_
            self._check_and_raise(node, 'id')

        self._check_and_raise(node, 'type')
        type_ = node['type'][2:]

        self._check_and_raise(self.templates, type_, ' in saved templates')

        template = copy.copy(self.templates[type_])
        template = template.replace('~', '_$name_')
        template_py = self.yaml.load(template)

        self._check_and_raise(template_py, 'args', 'in template ' + type_)

        args = self.get_args_without_self_dependenices(template_py['args'], node)
        replacements = self.get_optional_and_required_arguments(args, node)

        replacements = self.add_construct_replacements(replacements, args)

        template_py = self.yaml.load(template)

        if 'make' in template_py:
            replaced_args = {k[1:]: v for k, v in replacements.items()}
            self.apply_build_script(template_py['make'], replaced_args, template_py)
            template_py = self.yaml.load(self.yaml.dump(template_py).replace('~', '_$name_'))

        template_py = self.unpack_requirsevily(template_py, replacements)

        template_py.pop('args')

        extra_yaml = Templates.cyclicly_replace_args_in_text(replacements, self.yaml.dump(template_py))

        extra = self.yaml.load(extra_yaml)

        if 'view' in extra:
            if 'nodes' in extra and node['id'] in extra['nodes']:
                extra['nodes'][node['id']]['view'] = extra['view']
            extra.pop('view')

        if 'children' in extra:
            if 'nodes' in extra and node['id'] in extra['nodes']:
                if 'view' not in extra['nodes'][node['id']]:
                    extra['nodes'][node['id']]['view'] = dict()
                extra['nodes'][node['id']]['view']['children'] = extra['children']
            extra.pop('children')

        return extra

    def compile_all_nodes(self, nodes, lazy=False):
        if isinstance(nodes, str):
            nodes = self.yaml.load(nodes)
        if not isinstance(nodes, dict):
            raise RuntimeWarning('nodes in compile_all_nodes should be a dict (or yaml dict)')

        extra = {'nodes': nodes}
        while True:
            replaced = []
            for name, node_description in extra['nodes'].items():
                if 'type' not in node_description:
                    print(node_description)
                    raise RuntimeWarning('node ' + name + ' does not have a type field!')
                if node_description['type'][:2] == 't/':
                    replaced.append(self.compile_templated_node(node_description_yaml=self.yaml.dump(node_description),
                                                                 id_=name, lazy=lazy))

            if len(replaced) == 0:
                break
            else:
                extra = functools.reduce(Templates.merger.merge, replaced, extra)

        return extra

    def on_message(self, task):
        if 'templates' in task.keywords:
            templates = task.message
            if isinstance(templates, str):
                templates = self.yaml.load(task.message)
            if not isinstance(templates, dict):
                raise RuntimeWarning('templates section should be a dictionary')
            for name, template in templates.items():
                self.load_template(self.yaml.dump(template), name)
        if 'templated_nodes' in task.keywords:
            return Task(message=self.compile_all_nodes(task.message), keywords={'build'}, sender_name='templates')
