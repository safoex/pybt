from pybt.src.core.memory.memory import Memory
from bsagr import BeliefStateSimple
from ruamel import yaml
import copy
import sympy
from pybt.src.planner.belief_memory.belief_memory import BeliefMemory


class BeliefMemoryForSensitivityAnalysis(BeliefMemory):
    def __init__(self, physical_state, prob=1):
        super().__init__(physical_state, prob)

    def exec(self, leaf):
        res = super().exec(leaf)