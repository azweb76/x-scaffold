import plugins


class PluginA(plugins.Base):

    def __init__(self):
        pass

    def start(self):
        print("Plugin A")