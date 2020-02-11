from src.core.tree.behavior_tree import BehaviorTree
from src.planner.nodes.planning_node import PlanningSequential
from src.planner.belief_memory.belief_memory import BeliefMemory


class PlanningBehaviorTree(BehaviorTree):
    def __init__(self, name='behavior_tree', memory=None, root_node=None):
        super().__init__(name, memory, root_node, PlanningSequential)

    def tick(self, with_memory: BeliefMemory = None) -> BeliefMemory:
        memory = with_memory or self.memory
        return self.root.tick(memory)

    def verify(self, with_memory: BeliefMemory, ticks_limit=100, states_limit=100):
        memory = with_memory
        results = BeliefMemory([])
        ticks_counter = 0
        while 0 < len(memory.states) < states_limit and ticks_counter < ticks_limit:
            result = self.tick(memory)
            ended, memory = result.split_by(lambda s: result.action_key not in s or len(s[result.action_key]) == 0)
            results += ended
            ticks_counter += 1
            memory = memory.apply_delayed_actions()

        return results
