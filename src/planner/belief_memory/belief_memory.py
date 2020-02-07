from src.core.memory.memory import Memory
from bsagr import BeliefStateSimple
from ruamel import yaml
import copy


class BeliefMemory(BeliefStateSimple):
    state_key = '_S'
    action_key = '_A'
    action_history_key = '_AH'
    state_keywords = [
        'R', 'S'
    ]
    action_keywords = [
        'postconditions',
        'immediate'
    ]
    single_action_keywords = [
        'prob',
        'action'
    ]

    def __init__(self, physical_state=None, prob=1):
        super().__init__(physical_state or [], prob)
        self.builtins = None

    def _init_builtins(self):
        ps = {}
        exec("", ps)
        self.builtins = ps['__builtins__']
        ps.pop('__builtins__')
        return self.builtins

    def _eval(self, expression, physical_state):
        physical_state['__builtins__'] = self.builtins or self._init_builtins()
        res = eval(expression, physical_state)
        self.builtins = physical_state['__builtins__']
        physical_state.pop('__builtins__')
        return res

    def _exec(self, script, physical_state):
        physical_state['__builtins__'] = self.builtins or self._init_builtins()
        exec(script, physical_state)
        self.builtins = physical_state['__builtins__']
        physical_state.pop('__builtins__')

    @staticmethod
    def _is_leaf_a_condition(leaf):
        return 'R' in leaf or 'S' in leaf or \
               ('true_state' in leaf and 'false_state' in leaf and 'expression' in leaf)

    def build(self, expression):
        leaf = expression
        if isinstance(expression, str):
            leaf = yaml.safe_load(expression)
        if not isinstance(leaf, dict):
            raise RuntimeWarning("leaf in a BeliefMemory.build should be a dict (or yaml dumped dict)")

        if BeliefMemory._is_leaf_a_condition(leaf):
            for state in self.state_keywords:
                if state in leaf:
                    leaf[state] = Memory.unindent(leaf[state])
        else:
            for action_kw in self.action_keywords:
                if action_kw in leaf:
                    for action_def in leaf[action_kw]:
                        action_def['action'] = Memory.unindent(action_def['action'])

        return leaf

    def exec(self, leaf, apply_postconditions=False):
        if not isinstance(leaf, dict):
            raise RuntimeWarning("leaf in a BeliefMemory.exec should be a dict!")

        if BeliefMemory._is_leaf_a_condition(leaf):
            def func(ps):
                if 'true_state' in leaf:
                    return leaf['true_state'][0] if self._eval(leaf['expression'], ps) else leaf['false_state'][0]
                if 'R' in leaf and self._eval(leaf['R'], ps):
                    return 'R'
                return 'S' if self._eval(leaf['S'], ps) else 'F'

            return self.bucketize_with(func, self.state_key)
        else:
            # now support only postconditions
            for s, p in self.states:
                if 'postconditions' in leaf:
                    if apply_postconditions:
                        all_states = []
                        for effect in leaf['postconditions']:
                            prob, code = effect['prob'], effect['action']
                            code_for_func = code
                            if isinstance(code, dict):
                                code_for_func = sum([k + ' = ' + v + '\n' for k, v in code.items()])

                            def func(ps):
                                self._exec(code_for_func, ps)
                                if self.action_history_key not in ps:
                                    ps[self.action_history_key] = []
                                ps[self.action_history_key].append((leaf['id'], code_for_func))

                            bss = type(self)(copy.deepcopy(self.states), prob)
                            bss.apply_function(func)

                            all_states += bss.states
                        self.states = all_states
                    else:
                        s[self.state_key] = 'S'
                        if self.action_key not in s:
                            s[self.action_key] = [leaf]
                        else:
                            s[self.action_key].append(leaf)
                else:
                    s[self.state_key] = 'S'
                    self._exec(leaf['script'], s)
            self.simplify()
            return self

    def apply_delayed_actions(self):
        mem_res = BeliefMemory()
        for s, p in self.states:
            if self.action_key not in s:
                s[self.action_key] = []
        for actions, bss in self.bucketize(lambda x: yaml.safe_dump(x[self.action_key])):
            mem_tmp = bss
            for action in yaml.safe_load(actions):
                mem_tmp = mem_tmp.exec(action, apply_postconditions=True)
            mem_res += mem_tmp
        for s, p in mem_res.states:
            s.pop(self.action_key)
        mem_res.simplify()
        return mem_res

    def __deepcopy__(self, memo):
        return type(self)(copy.deepcopy(self.states))

    def __copy__(self):
        return type(self)(copy.copy(self.states))

    def bucketize_with(self, function, var='_S'):
        res = list(self.bucketize(function))
        for r, bss in res:
            bss.apply({var: r})
        bss = type(self)(res[0][1].states)
        for r, bs in res[1:]:
            bss += bs
        bss = copy.deepcopy(bss)
        bss.simplify()
        return bss


    def bucketize_by(self, key, pop=False):
        res = self.bucketize(lambda s: s[key])
        if not pop:
            return res
        else:
            res.apply_function(lambda s: s.pop(key) if key in s else None)
            return res




