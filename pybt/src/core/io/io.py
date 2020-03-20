from queue import PriorityQueue
from functools import total_ordering


@total_ordering
class Task:
    def __init__(self, message, sender_name, keywords=None, priority=None):
        """
        
        :param message: message to other channels, e.g. sensor data for BT
        :param sender_name: Channel id which send a message
        :param keywords: set() of keywords for sorting out recipients
        """
        self.message = message
        self.sender_name = sender_name
        if isinstance(message, dict) and keywords is None:
            keywords = set(message.keys())
        self.keywords = keywords or set()
        self.priority = priority or [0]

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def split_priority_to(self, replacement_task_index):
        return self.priority + [replacement_task_index]


class Channel:
    def __init__(self, name, keywords=None, _io=None):
        """
        
        :param name: 
        :param keywords: Channel will listen to this keywords. Channel won't subscribe to any keywords if None. 
        All except for set() instances shall be treated as boolean function which filters message to process 
        :param _io: IO object, can also be assigned by IO.reg() method 
        """
        self.name = name
        self.keywords = keywords or set()
        self._io = _io
        self.using_filter_function = not isinstance(keywords, set)

    def on_message(self, task):
        """
        If IO execute a task with keywords this channel subscribed on, this method will be called.
        :param task: a Task object (so it includes sender_name!)
        :return: should return either Task object or None. Otherwise generates an error
        """
        pass

    def send(self, message, keywords=None, priority=None):
        """
        send a message to self._io IO center
        :param message: data: message or whole Task. In latter case keywords and priority are ignored
        :param keywords: keywords for the task
        :param priority: priority for the task
        :return: None
        """
        if self._io is None:
            raise RuntimeWarning("Attempt to send " + message + " having self._io is None")
        else:
            if isinstance(message, Task):
                self._io.accept(message)
            else:
                self._io.accept(Task(message, self.name, keywords, priority))


class Hook(Channel):
    def __init__(self, name, keywords, hook_function):
        super().__init__(name, keywords, None)
        self.hook = hook_function

    def on_message(self, task):
        return self.hook(task)


class IO:
    def __init__(self):
        self.listeners = dict()
        self.keywords_to_listeners = dict()
        self.listeners_with_filter_function = set()
        self.tasks = PriorityQueue()
        self.task_counter = 0

    def reg(self, listener):
        if listener.name in self.listeners:
            raise RuntimeWarning("Listener already " + listener.name + " added!")

        self.listeners[listener.name] = listener
        if listener.using_filter_function:
            self.listeners_with_filter_function.add(listener)
        else:
            for keyword in listener.keywords:
                if keyword not in self.keywords_to_listeners:
                    self.keywords_to_listeners[keyword] = set()
                self.keywords_to_listeners[keyword].add(listener)

        listener._io = self

    def unreg(self, listener):
        if listener.name not in self.listeners:
            raise RuntimeWarning("Listener " + listener.name + " is not added or already unregistered!")

        self.listeners.pop(listener.name)
        if listener.using_filter_function:
            self.listeners_with_filter_function.remove(listener)
        else:
            for keyword in listener.keywords:
                self.keywords_to_listeners[keyword].remove(listener)
                if len(self.keywords_to_listeners[keyword]) == 0:
                    self.keywords_to_listeners.pop(keyword)

        listener._io = None

    def accept(self, task_s, move_to_end=True):
        """
        accepts task, puts it into the queue
        :param move_to_end: if set to False, preserve priority (to e.g., replace just executed task with new one).
            If True, task will be in the end of the queue
        :param task_s: a (list of) Task object or None
        :return: None
        """
        if isinstance(task_s, list):
            for task in task_s:
                self.accept(task, move_to_end)
        elif isinstance(task_s, Task):
            task = task_s
            if task is not None:
                if move_to_end:
                    task.priority = [self.task_counter]
                    self.task_counter = self.task_counter + 1
                self.tasks.put_nowait(task)
        elif task_s is not None:
            raise RuntimeWarning("task_s object should be Task or list of Task -s or None")

    def _get_listeners_for_task(self, task):
        listeners_to_be_called = set()

        for keyword in task.keywords:
            if keyword in self.keywords_to_listeners:
                for listener in self.keywords_to_listeners[keyword]:
                    listeners_to_be_called.add(listener)

        for listener in self.listeners_with_filter_function:
            if listener.keywords(task):
                listeners_to_be_called.add(listener)

        return listeners_to_be_called

    def _execute(self, task):
        for listener in self._get_listeners_for_task(task):
            self.accept(listener.on_message(task), move_to_end=False)

    def run(self, stop_function=None):
        """
        Blocking routine for IO class.
        :param stop_function: routine stops if stop_function() is False. E.g., ros.is_shutdown()
        :return:
        """
        stop = stop_function or (lambda: False)

        while not stop():
            self._execute(self.tasks.get())
            self.tasks.task_done()

    def run_all(self):
        """
        runs all the queue, equivalent to: self.run(stop_function=lambda: self.tasks.empty())
        :return:
        """
        self.run(stop_function=lambda: self.tasks.empty())
