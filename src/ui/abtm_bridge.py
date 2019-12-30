from abtm.abtm_app import ABTMApp
from src.core.io.io import Channel


class ABTMAppChannel(ABTMApp, Channel):
    def __init__(self):
        ABTMApp.__init__(self, rosparams=None, glade_file='../../../abtm_ui/abtm/abtm.glade')
        Channel.__init__(self, name='ui', keywords={'nodes_for_tree'})
        self.setup_all(with_ros=False, icon='../../../abtm_ui/abtm/abtm.png')

    def on_message(self, task):
        self.on_tree({"data": task.message})
