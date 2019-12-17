from ruamel import yaml
from definitions import ROOT_DIR


class Memory:
    def __init__(self):
        self.vars = {}
        with open(ROOT_DIR + '/src/core/memory/memory_setup.py') as ms:
            self.exec(ms.read())
        self.exec('__service__ = _Service()')
        self.service = self.vars['__service__']

    def exec(self, code, arg=None):
        if arg is not None:
            exec(code, self.vars, arg)
        else:
            exec(code, self.vars)

    def exec_service(self, code, arg=None):
        if arg is not None:
            self.exec('__service__.' + code + '(locals())', arg)
        else:
            self.exec('__service__.' + code + '()')

    def set(self, sample):
        self.exec_service('set', sample)
        self.exec_service('update')

    def add(self, sample):
        self.exec_service('set', sample)
        self.exec_service('add', sample)

    def changes(self):
        return self.service.changed

    def flush(self):
        self.exec_service('apply')
        self.exec_service('clear')

    def _action_function(self, expression):
        self.exec(expression)
        self.exec_service('update')

    def build_action(self, expression):
        return lambda: self._action_function(self._unindent(expression))

    def build_condition(self, expression):
        return lambda: eval(self._unindent(expression), self.vars)

    def print_vars(self):
        print(yaml.dump({k: self.vars[k] for k in self.service.track}))

    @staticmethod
    def _unindent(block, symbol=None):
        def symbols_from_beginning(string, _symbol='\t'):
            tabs = 0
            for c in string:
                if c == _symbol:
                    tabs += 1
                else:
                    break
            return tabs

        if symbol is None:
            return Memory._unindent(Memory._unindent(block, '\t'), ' ')

        block = "".join([line + '\n' for line in block.split('\n') if len(line)])
        block = block[:-1]

        min_indent = symbols_from_beginning(block, symbol)

        block_splitted = block.split('\n')
        for line in block_splitted:
            min_indent = min(min_indent, symbols_from_beginning(line, symbol))

        res = "".join([line[min_indent:] + '\n' for line in block_splitted[:-1]])
        res = res + block_splitted[-1][min_indent:]
        return res
