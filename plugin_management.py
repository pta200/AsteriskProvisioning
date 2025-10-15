import importlib.util
import os
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
    

class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = plugin_dir
        self.plugins = {}
        self._load_plugins()

    def _load_plugins(self):
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(module_name, os.path.join(self.plugin_dir, filename))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        for name in dir(module):
                            obj = getattr(module, name)
                            if isinstance(obj, type) and issubclass(obj, PluginBase) and obj is not PluginBase:
                                plugin_instance = obj()
                                self.plugins[plugin_instance.name] = plugin_instance
                except Exception as e:
                    print(f"Error loading plugin {module_name}: {e}")

    def get_plugin(self, name):
        return self.plugins.get(name)

    def list_plugins(self):
        return list(self.plugins.keys())
    
if __name__ == "__main__":
    manager = PluginManager()
    print("Available plugins:", manager.list_plugins())

    text = "Hello World"

    uppercase_plugin = manager.get_plugin("uppercase")
    if uppercase_plugin:
        processed_text = uppercase_plugin.run(text)
        print(f"Uppercase plugin output: {processed_text}")

    reverse_plugin = manager.get_plugin("reverse")
    if reverse_plugin:
        processed_text = reverse_plugin.run(text)
        print(f"Reverse plugin output: {processed_text}")
