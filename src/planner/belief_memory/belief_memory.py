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

    @staticmethod
    def _is_leaf_a_condition(leaf):
        return 'R' in leaf or 'S' in leaf

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
                if 'R' in leaf and eval(leaf['R'], ps):
                    return 'R'
                return 'S' if eval(leaf['S']) else 'F'

            return self.bucketize(func)
        else:
            # now support only postconditions
            all_states = []
            for effect in leaf['postconditions']:
                prob, code = effect['prob'], effect['code']

                def func(ps):
                    exec(code, ps)

                bss = BeliefMemory(copy.deepcopy(self.states), prob)
                all_states += bss.apply_function(func)
            result = BeliefMemory(all_states)
            result.simplify()
            return [('S', result)]
