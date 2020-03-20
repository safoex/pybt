from pybt.src.core.build.yaml.generic import GenericBuilder


class Memories(GenericBuilder):
    def __init__(self, memory):
        super().__init__('memory', {'memory', 'vars', 'variables', 'exec', 'execute'},
                         {'memory', 'vars', 'variables', 'exec', 'execute'})
        self.memory = memory

    def on_message(self, task):
        """

        :param task: a message should contain some of {'execute', 'exec', 'variables', 'vars'} sections
        :return: None
        """
        if 'exec' in task.keywords or 'execute' in task.keywords:
            self._build_exec(task.message)
        elif 'vars' in task.keywords or 'variables' in task.keywords:
            self._build_vars(task.message)
        elif 'memory' in task.keywords:
            self.build_modules(task)

    def _build_exec(self, message):
        """
        executes message inside self.memory
        :param message: a dict (with key 'exec' or 'execute') or list (with plain strings to execute) or str (code to
        execute)
        :return: None
        """
        if isinstance(message, dict):
            if 'exec' in message:
                message = message['exec']
            elif 'execute' in message:
                message = message['execute']

        if isinstance(message, list):
            for code in message:
                self._build_exec(code)

        elif isinstance(message, str):
            self.memory.exec(message)
        else:
            raise RuntimeWarning('execute/exec section of memory is not formatted properly')

    def _build_vars(self, message):
        """
        Adds and register vars in memory.
        :param message: a dict with pairs (key, str). Pairs shall be substituted as key = #str in Python code.
        :return: None
        """
        if isinstance(message, dict):
            for var_name, var_value in message.items():
                try:
                    var_value = str(var_value)
                except TypeError:
                    raise RuntimeWarning(
                        'Value of variable ' + var_name + ' should be a string (probably with a Python code)')
                self.memory.exec(var_name + ' = ' + var_value)

            self.memory.exec_service('add', message)

        else:
            raise RuntimeWarning('vars/variables section should a dictionary')
