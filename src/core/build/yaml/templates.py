from ruamel import yaml
import src.core.nodes.sequential as sequential
import src.core.nodes.leaf as leaf
from src.core.build.yaml.nodes import Nodes
import copy
import deepmerge
import functools


class Templates(Nodes):
    def __init__(self, memory):
        super().__init__(memory)
        self.templates = {}

    def load_template(self, template_yaml, name=None):
        """
        loads a yaml description of the template to memory
        :param template_yaml: yaml description of the template
        :param name: name of template
        :return: None
        """
        template = yaml.safe_load(template_yaml)

        if name is None:
            self._check_and_raise(template, 'name', 'in a template')
            name = template['name']

        self.templates[name] = template_yaml

    @staticmethod
    def any_arg_in_string(args, s):
        args = ['$' + k for k in args.keys()]
        for a in args:
            if a in s:
                return True
        return False

    @staticmethod
    def cyclicly_replace_args_in_text(replacements, text):
        while Templates.any_arg_in_string(replacements, text):
            for arg_name in replacements:
                if '$' + arg_name in text:
                    text.replace('$' + arg_name, str(replacements[arg_name]))

    @staticmethod
    def get_optional_and_required_arguments(args_py, node, template):
        reps = dict()

        reps['$name'] = '_' + id + '_'
        template.replace('~', reps['$name'])

        has_optional = 'optional' in args_py
        has_required = 'required' in args_py

        if has_required:
            for arg_name in args_py['required']:
                Nodes._check_and_raise(node, arg_name)
                reps['$' + arg_name] = node[arg_name]

        if has_optional:
            for arg_name in args_py['optional'].keys():
                if arg_name in node:
                    reps['$' + arg_name] = node[arg_name]
                else:
                    reps['$' + arg_name] = args_py['optional'][arg_name]

        return reps

    @staticmethod
    def get_args_without_self_dependenices(args_py):
        replacements = Templates.get_optional_and_required_arguments(args_py)

        args_text = yaml.dump(args_py)

        Templates.cyclicly_replace_args_in_text(replacements, args_text)
        args = yaml.safe_load(args_text)

        return args

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
                Templates.cyclicly_replace_args_in_text({'$V': old_value, '$K': str(k)}, new_value)
                result.append(new_value)
        elif isinstance(source, dict):
            result = {}
            for (old_key, old_value), (rep_V, rep_K) in zip(source.items(), rep_table):
                new_value = copy.copy(rep_V)
                new_key = copy.copy(rep_K)
                reps = {'$V': old_value, '$K': old_key}
                Templates.cyclicly_replace_args_in_text(reps, new_value)
                Templates.cyclicly_replace_args_in_text(reps, new_key)
                result[new_key] = new_value
        else:
            result = source

        return result

    def compile_templated_node(self, node_description_yaml, id_=None):
        """
        create a collection of nodes and variable declarations out of node_description
        :param node_description_yaml: yaml dict with description of templated node
        :param id_: id of node
        :return: a collection of nodes and variables (python dict {'nodes': {...}, 'vars': {...}})
        """
        node = yaml.safe_load(node_description_yaml)

        if 'id' not in node:
            node['id'] = id_
            self._check_and_raise(node, 'id')

        self._check_and_raise(node, 'type')
        type_ = node['type'][2:]

        self._check_and_raise(self.templates, type_, ' in saved templates')

        template = copy.copy(self.templates[type_])
        template_py = yaml.safe_load(template)

        self._check_and_raise(template, 'args', 'in template ' + type_)

        args = self.get_args_without_self_dependenices(template_py['args'])
        replacements = self.get_optional_and_required_arguments(args)

        has_construct = 'construct' in args

        if has_construct:
            for arg_name in args['construct'].keys():
                arg_def = args['construct'][arg_name]
                self._check_and_raise(arg_def, 'from', 'in construct for ' + arg_name)
                arg_name_from = arg_def['from']
                self._check_and_raise(args, arg_name_from, 'as a source for constructing ' + arg_name)
                source = args[arg_name_from]

                replacements['$' + arg_name] = Templates.replace_from(source, arg_def)

        template_py = yaml.load(template)

        while 'unpack' in template_py and isinstance(template_py['unpack'], dict):
            unpacked = [
                Templates.replace_from(args[arg_name], {'V': yaml.dump(to_unpack)})
                for arg_name, to_unpack in template_py['unpack'].items()
            ]
            template_py = functools.reduce(deepmerge.always_merger.merge, unpacked, template_py)

        Templates.cyclicly_replace_args_in_text(replacements, template)

        return {key: value for key, value in template_py.items() if key != 'args'}
