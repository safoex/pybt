# from src.core.memory.memory import Memory


class BehaviorTree(object):
    TICK = '__TICK__'
    ERASE = '__ERASE__'
    REPLACE = '__REPLACE__'
    INSERT = '__INSERT__'
    
    def __init__(self, memory, root_name="__ROOT__"):
        self.memory = memory
        self.root_name = root_name
        self.nodes = {}

    @staticmethod
    def is_command(sample):
        if isinstance(sample, dict):
            return BehaviorTree.ERASE in sample or BehaviorTree.REPLACE in sample or BehaviorTree.INSERT in sample
    
    def is_tick(self, sample):
        pass
        # if sample == BehaviorTree.tick
    
    def is_data(self, sample):
        return isinstance(sample, dict) and not self.is_command(sample)
        
    def execute(self, sample):
        if self.is_data(sample):
            self.memory.set(sample)
        elif self.is_tick(sample):
            return self.tick()
        elif self.is_command(sample):
            return self.apply_command(sample)
        
    def tick(self):
        self.nodes[self.root_name].tick()
        outputs = self.memory.changes()
        self.memory.flush()
        return outputs
    
    def apply_command(self, command):
        pass
