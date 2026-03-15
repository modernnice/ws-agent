import os
import yaml
from utils.path_tool import get_abs_path


class ConfigHandler:
    def __init__(self):
        self.configs = {}
        self._load_configs()

    def _load_configs(self):
        files = ["agent.yml", "chroma.yaml", "prompts.yml", "rag.yml"]
        for f in files:
            path = get_abs_path(os.path.join("config", f))
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as file:
                    self.configs[os.path.splitext(f)[0]] = yaml.safe_load(file) or {}

    def get(self, name, key=None, default=None):
        cfg = self.configs.get(name, {})
        return cfg.get(key, default) if key else cfg

config = ConfigHandler()

if __name__ == "__main__":
    print(f"Agent Config: {config.get('agent')}")
    print(f"Test Key: {config.get('agent', 'test_key')}")
