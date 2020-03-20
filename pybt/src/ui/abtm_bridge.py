from abtm_ui.abtm.abtm_app import ABTMApp
from pybt.src.core.io.io import Channel


class ABTMAppChannel(ABTMApp, Channel):
    def __init__(self):
        ABTMApp.__init__(self, rosparams=None)
        Channel.__init__(self, name='ui', keywords={'nodes_for_tree', 'states_update'})
        self.setup_all(with_ros=False)

    def on_message(self, task):
        if 'nodes_for_tree' in task.keywords:
            self.on_tree({"data": task.message})
        elif 'states_update' in task.keywords:
            self.on_states({'data': task.message})