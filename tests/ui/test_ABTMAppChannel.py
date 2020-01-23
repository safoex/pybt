from unittest import TestCase
from src.core.build.yaml.templates import Templates
from src.core.build.yaml.memories import Memories
from src.core.build.yaml.nodes import Nodes
from src.core.tree.behavior_tree import BehaviorTree
from src.core.build.yaml.generic import GenericBuilder
from src.core.memory.memory import Memory
from src.core.io.io import Task, IO
from src.ui.abtm_bridge import ABTMAppChannel
import threading
import time
import copy
from ruamel import yaml
import sys

class TestABTMAppChannel(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.templates = Templates(self.memory)
        self.io = IO()
        self.memories = Memories(self.memory)
        self.bt = BehaviorTree('behavior_tree', self.memory)
        self.nodes = Nodes(self.memory)
        self.generic = GenericBuilder('builder', {'build'}, ['memory', 'templates', 'vars', 'nodes'])
        self.io.reg(self.memories)
        self.io.reg(self.bt)
        self.io.reg(self.nodes)
        self.io.reg(self.generic)
        self.io.reg(self.templates)

    def test_viewer(self):
        all = """
                        vars:
                          time: 1
                          z: 2
                          reset_var: true
                          reset_move: true
                          uuid: 0
                          test_str: '""'
                          ENV: '"KEK"'

                        nodes:
                          root:
                            root: True
                            type: sequence
                            children: [env_branch, check_me, init_branch]                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                        
                          env_branch:                                                                                                                                           
                            type: action
                            script: ENV = 'ROS_SIM'

                          check_me:
                            type: action
                            script: test_str += 'Hey! '

                          init_branch:
                            type: t/seq_latches
                            children: [some, test, actions]
                            reset_var: reset_var

                          some:
                            type: action
                            script: test_str += 'some '

                          test:
                            type: action
                            script: test_str += 'test '

                          actions:
                            type: action
                            script: test_str += 'actions! (these actions done only once!) '

                        """
        tmplt = ""
        with open('../core/build/templates.yaml') as tmplt_file:
            tmplt = tmplt_file.read()
        self.viewer = ABTMAppChannel()
        self.io.reg(self.viewer)
        self.io.accept(Task(message=tmplt, keywords={'build'}, sender_name='anonymous'))
        self.io.accept(Task(message=all, keywords={'build'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.viewer_thread = threading.Thread(target=lambda: self.viewer.run())
        self.viewer_thread.start()
        time.sleep(1)
        self.io.run_all()
