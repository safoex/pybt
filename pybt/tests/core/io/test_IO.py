from unittest import TestCase
import pybt.src.core.io.io as io


class TestTask(TestCase):
    def setUp(self) -> None:
        pass

    def test_task_no_keywords(self):
        self.task = io.Task(
            message={
                'a': 2,
                'b': 3
            },
            sender_name='Evgenii'
        )
        self.assertEqual(len(self.task.keywords), 2)
        self.assertTrue('a' in self.task.keywords and 'b' in self.task.keywords)

    def test_task_keywords(self):
        self.task = io.Task(
            message={
                'a': 2,
                'b': 3
            },
            sender_name='Evgenii',
            keywords={'b'}
        )
        self.assertEqual(len(self.task.keywords), 1)
        self.assertTrue('a' not in self.task.keywords and 'b' in self.task.keywords)


class SaverChannel(io.Channel):
    def __init__(self, name, keywords=None, _io=None):
        super().__init__(name, keywords, _io)
        self.msgs = []

    def on_message(self, task):
        self.msgs.append(task)


class TestIO(TestCase):
    def setUp(self) -> None:
        self.io = io.IO()

    def test_channels_simple(self):
        self.ch1 = SaverChannel('mtv', {'music'})
        self.ch2 = SaverChannel('cnn', {'news'})
        self.io.reg(self.ch1)
        self.io.reg(self.ch2)
        self.ch2.send({'music': 'beetles'})
        self.ch1.send({'news': 'protests'})
        self.ch1.send({'music': 'queen', 'news': 'elections'})
        self.io.run_all()
        self.assertTrue(len(self.ch1.msgs), 2)
        self.assertTrue(len(self.ch2.msgs), 2)
        self.assertEqual(self.ch1.msgs[0].message['music'], 'beetles')
        self.assertEqual(self.ch1.msgs[1].message['music'], 'queen')
        self.assertEqual(self.ch2.msgs[0].message['news'], 'protests')
        self.assertEqual(self.ch2.msgs[1].message['news'], 'elections')

    def test_channels_filter(self):
        self.ch1 = SaverChannel('mtv', {'music'})
        self.ch2 = SaverChannel('cnn', lambda task: 'news' in task.message and 'music' not in task.message)
        self.io.reg(self.ch1)
        self.io.reg(self.ch2)
        self.ch2.send({'music': 'beetles'})
        self.ch1.send({'news': 'protests'})
        self.ch1.send({'music': 'queen', 'news': 'elections'})
        self.io.run_all()
        self.assertTrue(len(self.ch1.msgs), 2)
        self.assertTrue(len(self.ch2.msgs), 1)
        self.assertEqual(self.ch1.msgs[0].message['music'], 'beetles')
        self.assertEqual(self.ch1.msgs[1].message['music'], 'queen')
        self.assertEqual(self.ch2.msgs[0].message['news'], 'protests')
