import os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/pybt'


class State(object):
    RUNNING = 0
    SUCCESS = 1
    FAILURE = 2

    @staticmethod
    def Key(key):
        return '__STATE__' + key

    @staticmethod
    def from_str(string_rep):
        if string_rep[0] in ['S', 's']:
            return State.SUCCESS

        elif string_rep[0] in ['F', 'f']:
            return State.FAILURE

        elif string_rep[0] in ['R', 'r']:
            return State.RUNNING

        else:
            raise RuntimeWarning('Strange state keyword: ' + string_rep)

    @staticmethod
    def to_str(state_int):
        for i, string_rep in [(State.RUNNING, 'RUNNING'), (State.FAILURE, 'FAILURE'), (State.SUCCESS, 'SUCCESS')]:
            if state_int == i:
                return string_rep
        raise RuntimeWarning('State number should be in range [0,2]')
