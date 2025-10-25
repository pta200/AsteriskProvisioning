from plugins.plugins_base import PluginBase


class UppercasePlugin(PluginBase):
    def run(self, data):
        return data.upper()

    @property
    def name(self):
        return "uppercase"

class ReversePlugin(PluginBase):
    def run(self, data):
        return data[::-1]

    @property
    def name(self):
        return "reverse"