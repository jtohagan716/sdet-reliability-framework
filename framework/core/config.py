import yaml
from pathlib import Path


CONFIG_PATH = Path("config/dev.yaml")


def load_config():
    """
    Load configuration settings from YAML file.
    """
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)