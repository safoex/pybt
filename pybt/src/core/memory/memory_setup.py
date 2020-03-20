from ruamel import yaml
import copy


class _Service(object):
    def __init__(self):
        self.old = {}
        self.track = set()
        self.changed = set()

    def set(self, sample):
        globals().update(sample)

    @staticmethod
    def print_globals():
        print(globals().keys())

    def update(self):
        for k in self.track:
            if k not in self.changed:
                if self.test_for_change(k):
                    self.changed.add(k)

    def add(self, sample):
        if isinstance(sample, dict):
            for key in sample.keys():
                self.add(key)
        if isinstance(sample, str):
            self.track.add(sample)
            self.old[sample] = globals()[sample]

    def apply(self):
        for key in self.changed:
            self.old[key] = copy.deepcopy(globals()[key])

    def restore(self):
        for key in self.changed:
            globals()[key] = copy.deepcopy(self.old[key])
        self.clear()

    def clear(self):
        self.changed.clear()

    def push(self, key):
        self.changed.add(key)

    def test_for_change(self, key):
        return yaml.dump(globals()[key]) != yaml.dump(self.old[key])
