from src.core.io.io import Channel, Task
from ruamel import yaml


class GenericBuilder(Channel):
    def __init__(self, name, keywords, submodules_order=None):
        """

        :param name: name of builder e.g., 'memory'
        :param keywords: keywords it expects e.g., {'memory', 'vars'}
        :param submodules_order: submodules, that it could use. Has to be list (ordered)
        """
        super().__init__(name, keywords)
        self.submodules_order = submodules_order or list()

    def on_message(self, task):
        self.build_modules(task)

    def build_modules(self, task):
        msg = task.message
        if not isinstance(task.message, dict):  # and isinstance(task.message, str):
            msg = yaml.safe_load(task.message)

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
