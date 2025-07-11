import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "aliases.yaml")

def load_config(path=CONFIG_PATH):
    """
    Load the domain/alias config from a YAML file.
    Example YAML structure:
    domains:
      example.com:
        catch_all: user@gmail.com
        aliases:
          contact: user@gmail.com
          sales: sales@gmail.com
    """
    with open(path, "r") as f:
        return yaml.safe_load(f) 