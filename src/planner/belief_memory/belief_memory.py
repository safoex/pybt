from src.core.memory.memory import Memory
from bsagr import BeliefStateSimple
from ruamel import yaml
import copy


class BeliefMemory(BeliefStateSimple):
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

    def __init__(self, physical_state, prob=1):
        super().__init__(physical_state, prob)
        ps = physical_state
        if isinstance(physical_state, list):
            ps = physical_state[0][0]
        exec("", ps)
        self.builtins = ps['__builtins__']
        ps.pop('__builtins__')

    def _eval(self, expression, physical_state):
        physical_state['__builtins__'] = self.builtins
        res = eval(expression, physical_state)
        self.builtins = physical_state['__builtins__']
        physical_state.pop('__builtins__')
        return res

    def _exec(self, script, physical_state):
        physical_state['__builtins__'] = self.builtins
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

    def exec(self, leaf):
        if not isinstance(leaf, dict):
            raise RuntimeWarning("leaf in a BeliefMemory.exec should be a dict!")

        if BeliefMemory._is_leaf_a_condition(leaf):
            def func(ps):
                if 'true_state' in leaf:
                    return leaf['true_state'][0] if self._eval(leaf['expression'], ps) else leaf['false_state'][0]
                if 'R' in leaf and self._eval(leaf['R'], ps):
                    return 'R'
                return 'S' if self._eval(leaf['S'], ps) else 'F'

            return self.bucketize(func)
        else:
            # now support only postconditions
            all_states = []
            for effect in leaf['postconditions']:
                prob, code = effect['prob'], effect['action']

                def func(ps):
                    self._exec(code, ps)

                bss = type(self)(copy.deepcopy(self.states), prob)
                bss.apply_function(func)
                all_states += bss.states
            self.states = all_states
            self.simplify()
            return [('S', self)]

    def __deepcopy__(self, memo):
        return type(self)(copy.deepcopy(self.states))

    def __copy__(self):
        return type(self)(copy.copy(self.states))

