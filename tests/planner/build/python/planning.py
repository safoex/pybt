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
                children: [~started, __preconditions__, ~set_started, ~action, ~running]

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
                script: ~finished = False; ~started = True; __A_return_var = "~finished";
                immediate:
                    ~finished: False
                    ~started: True
                    
            ~running:
                type: condition
                expression: True
                true_state: RUNNING
                false_state: RUNNING
                
        children: []

    """

    if preconditions is not None and isinstance(preconditions, list) and len(preconditions) > 0:

        preconditions_listing = ""
        for i, prec in enumerate(preconditions):
            prec_id = '~prec_' + str(i)
            preconditions_listing += prec_id + ', '
        yml = yml.replace('__preconditions__,', preconditions_listing)

        pyobj = yaml.safe_load(yml)


        for i, prec in enumerate(preconditions):
            prec_id = '~prec_' + str(i)
            pyobj['nodes'][prec_id] = prec
            # pyobj['children'].append(prec_id)
    else:
        yml = yml.replace('__preconditions__,', ' ')

        pyobj = yaml.safe_load(yml)

    for pc in postconditions:
        pc.update({'~finished': 'True'})
        if isinstance(pc['prob'], str):
            z = {'z': 0}
            exec('z = ' + pc['prob'], {}, z)
            pc['prob'] = z['z']
    pyobj['nodes']['~action']['postconditions'] = postconditions
    pyobj['children'].append('~action')
    return pyobj


def make_wipe_action(place, objects):
    yml = """
    nodes:
        $name:
            postconditions:
              - place: ANY
                prob: 1
    """
    pyobj = yaml.safe_load(yml)
    for obj in objects:
        pyobj['nodes']['$name']['postconditions'][0]['has_no['+place+']['+obj+"]"] = 'RUNNING'
        pyobj['nodes']['$name']['postconditions'][0]['wiped['+place+']['+obj+"]"] = 'SUCCESS'
    return pyobj


