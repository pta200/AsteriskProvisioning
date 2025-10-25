import importlib.util
import os
import sys
from abc import ABC, abstractmethod
from plugins.plugins_base import PluginBase
    
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
                        sys.modules[spec.name] = module  # Add to sys.modules
                        spec.loader.exec_module(module)

                        # for name in dir(module):
                        for name, obj in module.__dict__.items():
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
