from unittest import TestCase
from pybt.src.core.build.yaml.templates import Templates
from pybt.src.core.build.yaml.memories import Memories
from pybt.src.core.build.yaml.nodes import Nodes
from pybt.src.core.tree.behavior_tree import BehaviorTree
from pybt.src.core.build.yaml.generic import GenericBuilder
from pybt.src.core.memory.memory import Memory
from pybt.src.core.io.io import Task, IO
from pybt.src.core.build.yaml.imports import Import


class TestImport(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.templates = Templates(self.memory)

    def test_all_inclusive_plus_import(self):
        all = """
                import:
                    - /tests/core/build/imports/funcs_for_import.py
                    
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
                    script: test_str = summary(test_str, 'Hey! ')

                  init_branch:
                    type: t/seq_latches
                    children: [some, test, actions]
                    reset_var: reset_var

                  some:
                    type: action
                    script: test_str = summary(test_str, 'some ')

                  test:
                    type: action
                    script: test_str += 'test '

                  actions:
                    type: action
                    script: test_str += 'actions! (these actions done only once!) '

                """
        tmplt = ""
        with open('templates.yaml') as tmplt_file:
            tmplt = tmplt_file.read()

        self.io = IO()
        self.memories = Memories(self.memory)
        self.bt = BehaviorTree('behavior_tree', self.memory)
        self.nodes = Nodes(self.memory)
        self.importer = Import(self.memory)
        self.generic = GenericBuilder('builder', {'build'}, ['build', 'import', 'memory', 'templates', 'vars', 'nodes'])
        self.io.reg(self.memories)
        self.io.reg(self.bt)
        self.io.reg(self.nodes)
        self.io.reg(self.generic)
        self.io.reg(self.importer)
        self.io.reg(self.templates)
        self.io.accept(Task(message=tmplt, keywords={'build'}, sender_name='anonymous'))
        self.io.accept(Task(message=all, keywords={'build'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.run_all()
        self.assertEqual('Hey! ' + 'some ' + 'test ' + 'actions! (these actions done only once!) ' + 'Hey! ' + 'Hey! ',
                         self.memory.vars['test_str'])
