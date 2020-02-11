from unittest import TestCase
from src.core.build.yaml.templates import Templates
from src.core.build.yaml.memories import Memories
from src.core.build.yaml.nodes import Nodes
from src.core.tree.behavior_tree import BehaviorTree
from src.core.build.yaml.generic import GenericBuilder
from src.core.memory.memory import Memory
from src.core.build.yaml.imports import Import
from src.core.io.io import Task, IO
import copy
from ruamel import yaml
import sys

class TestTemplates(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.templates = Templates(self.memory)

    def test_load(self):
        self.tmplt = """
        args:
          optional:
            S: True
            F: True
    
        nodes:
          $name:
            type: skipper
            children: [~SR, ~FR]
            view:
              S: $S
              F: $F
    
          ~SR:
            type: condition
            expr: $S
            true_state: SUCCESS
            false_state: RUNNING
    
          ~FR:
            type: condition
            expr: $F
            true_state: FAILURE
            false_state: RUNNING
    
        children: []
        """
        self.templates.load_template(self.tmplt, name='condition')
        self.assertEqual(self.templates.templates['condition'], self.tmplt)

    def test_misc1(self):
        # test self.templates.cyclicly_replace_args_in_text()
        self.test_load()
        self.assertTrue(self.templates.any_arg_in_string({'S': '1+1'}, self.tmplt))
        self.assertFalse(self.templates.any_arg_in_string({'D': '1+1'}, self.tmplt))
        tmplt_rep = copy.copy(self.tmplt)
        tmplt_rep = tmplt_rep.replace('$S', '1+1')
        self.assertEqual(self.templates.cyclicly_replace_args_in_text({'$S': '1+1'}, self.tmplt), tmplt_rep)

    def test_misc2(self):
        tmplt = """
        args:
          required: [child_sim, child_real]
          optional:
            env: $child_sim
    
        nodes:
          $name:
            type: selector
            children: [~select_ros_sim, $child_real]
    
          ~select_ros_sim:
            type: sequence
            children: [~if_ros_sim, $child_sim]
    
          ~if_ros_sim:
            type: condition
            expr: $env == ROS_SIM
            true_state: S
            false_state: F
    
        children: [$child_sim, $child_real]
        """
        node_req = """
        id: test_node
        type: t/select_ros_env
        child_sim: A_sim
        child_real: A_real
        """
        node_opt = """
        id: test_node
        type: t/select_ros_env
        child_sim: A_sim
        child_real: A_real
        env: ROS
        """
        self.templates.load_template(tmplt, name="select_ros_env")
        template_py = yaml.safe_load(self.templates.templates['select_ros_env'])
        args_py = self.templates.get_args_without_self_dependenices(template_py['args'], yaml.safe_load(node_req))
        reps = self.templates.get_optional_and_required_arguments(args_py, yaml.safe_load(node_req))
        reps_expected = {
            '$env': 'A_sim',
            '$child_sim': 'A_sim',
            '$child_real': 'A_real',
            '$name': "test_node"
        }
        self.assertEqual(reps_expected, reps)

        args_py = self.templates.get_args_without_self_dependenices(template_py['args'], yaml.safe_load(node_opt))
        reps = self.templates.get_optional_and_required_arguments(args_py, yaml.safe_load(node_opt))
        reps_expected = {
            '$env'       : 'ROS',
            '$child_sim' : 'A_sim',
            '$child_real': 'A_real',
            '$name'      : "test_node"
        }
        self.assertEqual(reps_expected, reps)

    def test_construct(self):
        tmplt = """
        args:
          required: [children, control_type]
          construct:
            _children_latched:
              from: children
              V: $V_latch
          view_exclude: [children]
    
        nodes:
          $name:
            type: $control_type
            children: $_children_latched
    
        unpack:
          children:
            nodes:
              $V_latch:
                type: t/latch
                child: $V
    
        children: $children
        """
        self.templates.load_template(tmplt, name="test")
        template_py = yaml.safe_load(self.templates.templates['test'])
        node = """
        id: test2
        type: t/test
        children: [A, B, C]
        control_type: skipper
        """
        args_py = self.templates.get_args_without_self_dependenices(template_py['args'], yaml.safe_load(node))
        reps = self.templates.get_optional_and_required_arguments(args_py, yaml.safe_load(node))
        reps = self.templates.add_construct_replacements(reps, args_py)
        self.assertEqual(reps['$_children_latched'], ['A_latch', 'B_latch', 'C_latch'])

    def test_unpack(self):
        tmplt_latch = """
        args:
          required: [child]
    
        vars:
          __STATE__$child: "UNDEFINED"
    
        nodes:
          $name:
            type: skipper
            children: [~mask, $child]
    
          ~mask:
            parent: $name
            type: t/condition
            S: __STATE__$child == SUCCESS
            F: __STATE__$child == FAILURE
    
        children: [$child]        
        """
        tmplt = """
                args:
                  required: [children, control_type]
                  construct:
                    _children_latched:
                      from: children
                      V: $V_latch
                  view_exclude: [children]

                nodes:
                  $name:
                    type: $control_type
                    children: $_children_latched

                unpack:
                  children:
                    nodes:
                      $V_latch:
                        type: t/latch
                        child: $V

                children: $children
                """
        self.templates.load_template(tmplt, name="control_latches")
        self.templates.load_template(tmplt_latch, name="latch")
        template_py = yaml.safe_load(self.templates.templates['control_latches'])
        node = """
                id: test2
                type: t/control_latches
                children: [A, B, C]
                control_type: skipper
                """
        args_py = self.templates.get_args_without_self_dependenices(template_py['args'], yaml.safe_load(node))
        reps = self.templates.get_optional_and_required_arguments(args_py, yaml.safe_load(node))
        reps = self.templates.add_construct_replacements(reps, args_py)
        templated_node = self.templates.unpack_requirsevily(template_py, reps)
        self.assertTrue('A_latch' in templated_node['nodes'])
        self.assertEqual(templated_node['nodes']['A_latch'], {'child': 'A', 'type': 't/latch'})

    def test_compile_node(self):
        tmplt_latch = """
                args:
                  required: [child]

                vars:
                  __STATE__$child: RUNNING

                nodes:
                  $name:
                    type: skipper
                    children: [~mask, $child]

                  ~mask:
                    parent: $name
                    type: t/condition
                    S: __STATE__$child == SUCCESS
                    F: __STATE__$child == FAILURE

                children: [$child]        
                """
        tmplt = """
                        args:
                          required: [children, control_type]
                          construct:
                            _children_latched:
                              from: children
                              V: $V_latch

                        nodes:
                          $name:
                            type: $control_type
                            children: $_children_latched
                            view: 
                                children: $children

                        unpack:
                          children:
                            nodes:
                              $V_latch:
                                type: t/latch
                                child: $V
                        """
        self.templates.load_template(tmplt, name="control_latches")
        self.templates.load_template(tmplt_latch, name="latch")
        template_py = yaml.safe_load(self.templates.templates['control_latches'])
        node = """
            type: t/control_latches
            children: [A, B, C]
            control_type: skipper
            """
        compiled_node = self.templates.compile_templated_node(node_description_yaml=node, id_='kek')
        # print(compiled_node)

    def test_compile_all_nodes(self):
        nodes = """
          ro:
            root: True
            type: sequence
            children: [env_branch, init_branch]
        
          env_branch:
            type: action
            expr: ENV = ROS_SIM
        
          init_branch:
            type: t/seq_latches
            children: [some, test, actions]
            reset_var: reset_var
        
          some:
            type: action
            expr: test_str.data += 'some '
        
          test:
            type: action
            expr: test_str.data += 'test '
        
          actions:
            type: action
            expr: test_str.data += 'actions! (these actions done only once!)'        
        """
        tmplt = ""
        with open('templates.yaml') as tmplt_file:
            tmplt = tmplt_file.read()
        # self.templates.on_message(Task(message=tmplt, keywords={'templates'}, sender_name='anonymous'))
        # response = self.templates.on_message(Task(message=nodes, keywords={'nodes', 'templated_nodes'}, sender_name='anonymous'))
        yml = yaml.YAML()
        yml.indent(mapping=4, sequence=4, offset=2)

        # yml.dump(response.message, stream=sys.stdout)


    def test_all_inclusive(self):
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
        with open('templates.yaml') as tmplt_file:
            tmplt = tmplt_file.read()

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
        self.io.accept(Task(message=tmplt, keywords={'build'}, sender_name='anonymous'))
        self.io.accept(Task(message=all, keywords={'build'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
        self.io.run_all()
        self.assertEqual('Hey! ' + 'some ' + 'test ' + 'actions! (these actions done only once!) ' + 'Hey! ' + 'Hey! ',
                         self.memory.vars['test_str'])

    # def test_all_inclusive_plus_import_plus_make(self):
    #     all = """
    #             import:
    #                 - /tests/core/build/imports/funcs_for_import.py
    #                 - /tests/core/build/imports/funcs_for_make.py
    #
    #             vars:
    #                 time: 0
    #                 Z: 0
    #
    #             nodes:
    #                 root:
    #                     root: True
    #                     type: sequence
    #                     children: [A1, A2]
    #
    #                 A1:
    #                     type: t/planning_action
    #                     preconditions:
    #                         -   S: time >= 0
    #                         -   R: Z != 0
    #                             S: Z > 0
    #                     script:
    #                         time = 2;
    #                         Z = 2;
    #                     postconditions:
    #                         -   action: Z = 2; time = 2;
    #                             prob: 1
    #
    #                 A2:
    #                     type: t/planning_action
    #                     preconditions:
    #                         - S: time > 2
    #                     script:
    #                         time = 0
    #                     postconditions:
    #                         -   action: time = 0;
    #                             prob: 1
    #
    #             """
    #     tmplt = ""
    #     with open('templates.yaml') as tmplt_file:
    #         tmplt = tmplt_file.read()
    #
    #     self.io = IO()
    #     self.memories = Memories(self.memory)
    #     self.bt = BehaviorTree('behavior_tree', self.memory)
    #     self.nodes = Nodes(self.memory)
    #     self.importer = Import(self.memory)
    #     self.generic = GenericBuilder('builder', {'build'}, ['build', 'import', 'memory', 'templates', 'vars', 'nodes'])
    #     self.io.reg(self.memories)
    #     self.io.reg(self.bt)
    #     self.io.reg(self.nodes)
    #     self.io.reg(self.generic)
    #     self.io.reg(self.importer)
    #     self.io.reg(self.templates)
    #     self.io.accept(Task(message=tmplt, keywords={'build'}, sender_name='anonymous'))
    #     self.io.accept(Task(message=all, keywords={'build'}, sender_name='anonymous'))
    #     self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
    #     self.io.accept(Task(message={'Z': 1}, keywords={'behavior_tree'}, sender_name='anonymous'))
    #     self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
    #     self.io.accept(Task(message={'Z': 3}, keywords={'behavior_tree'}, sender_name='anonymous'))
    #     self.io.accept(Task(message=BehaviorTree.TICK, keywords={'behavior_tree'}, sender_name='anonymous'))
    #     self.io.run_all()
    #     self.assertEqual(0, self.memory.vars['time'])



