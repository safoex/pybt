from pybt.src.core.build.yaml.generic import GenericBuilder
from ruamel import yaml
from pybt.src.core.io.io import Task
from definitions import ROOT_DIR


class Import(GenericBuilder):
    def __init__(self, memory):
        super().__init__('import', {'import'})
        self.memory = memory

    def on_message(self, task):
        """

        :param task: should be a list (or yaml -list)
        :return:
        """
        message = self.yaml.load(task.message) if isinstance(task.message, str) else task.message

        for sub_order, file in enumerate(message):
            if not isinstance(file, str):
                raise RuntimeWarning("all fields of import list should be strings with file paths!")
            with open(ROOT_DIR + file) as extra_file:
                if file[-4:] == '.yml' or file[-5:] == '.yaml':
                    keyword = 'build'
                elif file[-3:] == '.py':
                    keyword = 'execute'
                else:
                    raise RuntimeWarning('only .py and .yaml/.yml files could be imported!')
                self._io.accept(Task({keyword: extra_file.read()}, sender_name=self.name, keywords={keyword},
                                     priority=task.split_priority_to(sub_order)), move_to_end=False)

