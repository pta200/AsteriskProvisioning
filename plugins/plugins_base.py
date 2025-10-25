from abc import ABC, abstractmethod

class PluginBase(ABC):
    @abstractmethod
    def run(self, data):
        """Processes the given data using the plugin's logic."""
        pass

    @property
    @abstractmethod
    def name(self):
        """Returns the name of the plugin."""
        pass