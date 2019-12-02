class State(object):
    RUNNING = 0
    SUCCESS = 1
    FAILURE = 2
    Key = lambda key: '__STATE__' + key
