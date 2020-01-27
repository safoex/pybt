from src.core.tree.behavior_tree import BehaviorTree
from src.planner.nodes.planning_node import PlanningSequential
from bsagr import BeliefStateSimple as BSS


class PlanningBehaviorTree(BehaviorTree):
    def __init__(self, name='behavior_tree', memory=None, root_node=None):
        super().__init__(name, memory, root_node, PlanningSequential)
        
    def tick(self, with_memory=None):
        memory = with_memory or self.memory
        try:
            return self.root.tick(memory)
        except BaseException:
            return [('F', memory)] 
        
    def verify(self, with_memory=None, with_bt=None, ticks_limit=1000, substates_limit=1000, drop_failures=True):
        memory = with_memory or self.memory
        
        ticks_count = 0
        prob = 1
        probs = {
            'S': 0,
            'F': 0,
            'R': 0
        }
        report = []
        while ticks_count < ticks_limit:
            buckets = dict(self.tick(memory))

            if with_bt is not None:
                mem = None
                if 'S' in buckets and 'R' in buckets:
                    mem = buckets['R'] | buckets['S']
                elif 'S' in buckets:
                    mem = buckets['S']
                elif 'R' in buckets:
                    mem = buckets['R']
                if mem is not None:
                    measured_buckets = with_bt.tick(mem)
                    for k in ['S','R']:
                        if k in measured_buckets:
                            buckets[k] = measured_buckets[k]
                        else:
                            buckets.pop(k)
                    if 'F' in measured_buckets:
                        if 'F' in buckets:
                            buckets['F'] = buckets['F'] or measured_buckets['F']
                        else:
                            buckets['F'] = measured_buckets['F']

            if 'S' not in buckets and 'R' not in buckets:
                probs['F'] += sum(prob for state, prob in buckets['F'].states)
                report.append()

            if len(memory.states) > substates_limit:
                break
                
