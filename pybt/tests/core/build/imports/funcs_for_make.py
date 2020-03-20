from ruamel import yaml

__precondition__counter__ = 0


def action_with_preconditions(preconditions, script, postconditions):
    yml = """
        nodes: 
            $name: 
                type: sequence
                children: __to_be_replaced_with_children__
            
            ~action:
                type: action
                script: __to_be_replaced_with_script__
                postconditions: __to_be_replaced_with_postconditions__
    """
    tmplt_py = yaml.safe_load(yml)
    tmplt_py['nodes']['~action']['script'] = script
    tmplt_py['nodes']['~action']['postconditions'] = postconditions
    tmplt_py['nodes']['~action']['preconditions'] = preconditions
    children_list = []
    for c, args in preconditions.items():
        global __precondition__counter__
        __precondition__counter__ += 1
        name = '~precondition_' + str(__precondition__counter__)
        templated_precondition_i = {
            'type': 't/' + c
        }
        templated_precondition_i.update(args)
        tmplt_py['nodes'][name] = templated_precondition_i
        children_list.append(name)

    tmplt_py['children'] = children_list.copy()
    children_list.append('~action')
    tmplt_py['nodes']['$name']['children'] = children_list
    return tmplt_py


def make_action(preconditions, script, immediate, postconditions):
    yml = """
        var:
            ~started: False
            ~finished: False
            
        nodes:
            $name:
                type: skipper
                children: [~finished, ~seq]
            
            ~ended:
                type: condition
                true_state: SUCCESS
                fail_state: RUNNING
                expression: ~finished
            
            ~seq:
                type: sequence
                children: [~started, __preconditions__, ~action, ~set_started]
            
            ~started:
                type: condition
                true_state: RUNNING
                fail_state: FAILURE
                expression: ~started
            
            ~action:
                type: action
                script: $script
                immediate: $immediate
                postconditions: __postconditions__
                
            ~set_started:
                type: action
                script: ~finished = False; ~started = True;
                immediate:
                    ~finished: False
                    ~started: True
                
    """

    if preconditions is not None and isinstance(preconditions, list) and len(preconditions) > 0:
        preconditions_listing = ""
        for i, prec in preconditions:
            prec_id = '~prec_' + i
            preconditions_listing += prec_id + ', '
        yml.replace('__preconditions__', preconditions_listing)

        pyobj = yaml.safe_load(yml)
        pyobj['nodes']['~action']['postconditions'] = postconditions

        for i, prec in preconditions:
            prec_id = '~prec_' + i
            pyobj['nodes'][prec_id] = prec
    else:
        pyobj = yaml.safe_load(yml)
    return pyobj


def make_precondition(var, val, fail_state, obs):
    yml = """
        nodes:
            $name:
                type: __control__type__
                children: [~cond]
            ~cond:
                type: condition
                true_state: SUCCESS
                fail_state: $fail_state
                expression: $var == $val
                var: $var
                val: $val
    """
    control_type = "skipper" if fail_state == "RUNNING" else "selector"
    yml.replace('__control__type__', control_type)
    pyobj = yaml.safe_load(yml)
    if obs is not None:
        pyobj['nodes']['$name']['children'] = ['~prec', '~cond']
        pyobj['nodes']['~prec'] = obs
    return pyobj
