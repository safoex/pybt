from ruamel import yaml


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
    for i, c in enumerate(preconditions):
        templated_precondition_i = {
            'type': 't/condition',
        }
        if 'R' in c:
            templated_precondition_i['S'] = 'not (' + c['R'] + ') and (' + c['S'] + ')'
            templated_precondition_i['F'] = 'not (' + c['R'] + ') and not(' + c['S'] + ')'
        else:
            templated_precondition_i['S'] = c['S']
        name = '~precondition_' + str(i)
        tmplt_py['nodes']['~precondition_' + str(i)] = templated_precondition_i
        children_list.append(name)

    tmplt_py['children'] = children_list.copy()
    children_list.append('~action')
    tmplt_py['nodes']['$name']['children'] = children_list
    return tmplt_py
