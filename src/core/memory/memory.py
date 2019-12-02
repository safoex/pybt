from ruamel import yaml


class Memory:
    def __init__(self):
        self.vars = {}
        with open('memory_setup.py') as ms:
            self.exec(ms.read())
        self.exec('__service__ = _Service()')
        self.service = self.vars['__service__']
    
    def exec(self, func, arg=None):
        if arg is not None:
            exec(func, self.vars, arg)
        else:
            exec(func, self.vars)
        
    def exec_service(self, func, arg=None):
        if arg is not None:
            self.exec('__service__.'+func+'(locals())', arg)
        else:
            self.exec('__service__.'+func+'()')
    
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
        return lambda: self._action_function(expression)
    
    def build_condition(self, expression):
        return lambda: eval(expression, self.vars)
    
    def print_vars(self):
        print(yaml.dump({k: self.vars[k] for k in self.service.track}))
