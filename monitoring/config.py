import os
import json


# _default_config_path = os.path.join(os.path.dirname(__file__), "config.json")

def get_config(config_file = None):
    config_file = config_file or "config.json"
    if not os.path.isabs(config_file):
        config_file = os.path.join(os.path.dirname(__file__), config_file)
    
    with open(config_file, "r") as read_stream:
        return json.load(read_stream)
