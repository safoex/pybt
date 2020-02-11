from ruamel import yaml


def make_action(preconditions, script, immediate, postconditions):
    yml = """
        var:
            ~started: False
            ~finished: False

        nodes:
            $name:
                type: skipper
                children: [~finished, ~seq]

            ~finished:
                type: condition
                true_state: SUCCESS
                false_state: RUNNING
                expression: ~finished

            ~seq:
                type: sequence
                children: [~started, __preconditions__, ~action, ~set_started]

            ~started:
                type: condition
                true_state: RUNNING
                false_state: SUCCESS
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
        for i, prec in enumerate(preconditions):
            prec_id = '~prec_' + str(i)
            preconditions_listing += prec_id + ', '
        yml = yml.replace('__preconditions__,', preconditions_listing)

        pyobj = yaml.safe_load(yml)
        for pc in postconditions:
            pc.update({'~finished': 'True'})
        pyobj['nodes']['~action']['postconditions'] = postconditions

        for i, prec in enumerate(preconditions):
            prec_id = '~prec_' + str(i)
            pyobj['nodes'][prec_id] = prec
    else:
        yml = yml.replace('__preconditions__,', ' ')

        pyobj = yaml.safe_load(yml)
        pyobj['nodes']['~action']['postconditions'] = postconditions

    return pyobj


def make_precondition(var, val, false_state, obs):
    yml = """
        nodes:
            $name:
                type: __control__type__
                children: [~cond]
            ~cond:
                type: condition
                true_state: SUCCESS
                false_state: $false_state
                expression: "'$var == $val'"
                var: "'$var'"
                val: "'$val'"
    """
    control_type = "skipper" if false_state == "RUNNING" else "selector"
    yml = yml.replace('__control__type__', control_type)
    pyobj = yaml.safe_load(yml)
    if obs is not None and obs != 'None':
        pyobj['nodes']['$name']['children'] = ['~prec', '~cond']
        pyobj['nodes']['~prec'] = obs
    return pyobj
