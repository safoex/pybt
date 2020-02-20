from src.core.io.io import Channel, Task
from ruamel import yaml
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


def process_scalar(self):
    if self.analysis is None:
        self.analysis = self.analyze_scalar(self.event.value)
    if self.style is None:
        self.style = self.choose_scalar_style()
    split = (not self.simple_key_context)
    # VVVVVVVVVVVVVVVVVVVV added
    if split:  # not a key
        is_string = True
        if self.event.value and self.event.value[0].isdigit():
            is_string = False
        # insert extra tests for scalars that should not be ?
        if is_string:
            self.style = "'"
    # ^^^^^^^^^^^^^^^^^^^^
    # if self.analysis.multiline and split    \
    #         and (not self.style or self.style in '\'\"'):
    #     self.write_indent()
    if self.style == '"':
        self.write_double_quoted(self.analysis.scalar, split)
    elif self.style == '\'':
        self.write_single_quoted(self.analysis.scalar, split)
    elif self.style == '>':
        self.write_folded(self.analysis.scalar)
    elif self.style == '|':
        self.write_literal(self.analysis.scalar)
    else:
        self.write_plain(self.analysis.scalar, split)
    self.analysis = None
    self.style = None
    if self.event.comment:
        self.write_post_comment(self.event)


class YamlFixingQuotesLoader:
    def __init__(self):
        self.dd = yaml.RoundTripDumper
        self.dd.process_scalar = process_scalar

    def load(self, yaml_str):
        return yaml.load(yaml_str, Loader=yaml.RoundTripLoader)

    def dump(self, py_obj):
        return yaml.dump(py_obj, Dumper=self.dd)


class YamlLoader:
    def __init__(self):
        self.yaml2 = YAML()
        self.yaml2.indent(mapping=2, sequence=2, offset=0)


    def load(self, yaml_str):
        return yaml.safe_load(yaml_str)

    def dump(self, py_obj):
        stream = StringIO()
        self.yaml2.dump(py_obj, stream)
        return stream.getvalue()


class GenericBuilder(Channel):
    def __init__(self, name, keywords, submodules_order=None):
        """

        :param name: name of builder e.g., 'memory'
        :param keywords: keywords it expects e.g., {'memory', 'vars'}
        :param submodules_order: submodules, that it could use. Has to be list (ordered)
        """
        super().__init__(name, keywords)
        self.submodules_order = submodules_order or list()
        # self.yaml = YamlFixingQuotesLoader()
        self.yaml = YamlLoader()

    def on_message(self, task):
        self.build_modules(task)

    def build_modules(self, task):
        msg = task.message
        if not isinstance(task.message, dict):  # and isinstance(task.message, str):
            msg = self.yaml.load(task.message)

        sub_order = 0
        for submodule in self.submodules_order:
            submodule_key = None
            if isinstance(submodule, list):
                for submodule_alias in submodule:
                    if submodule_alias in msg:
                        submodule_key = submodule_alias

            if isinstance(submodule, str) and submodule in msg:
                submodule_key = submodule

            if submodule_key is not None:
                self._io.accept(Task(msg[submodule_key], sender_name=self.name, keywords={submodule_key},
                                     priority=task.split_priority_to(sub_order)), move_to_end=False)
                sub_order += 1
