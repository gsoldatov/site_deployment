import os
import json


def get_config(config_file = None):
    """
    Reads and deserializes monitoring configuration from `config_file`.
    If omitted, reads from `config.json` in the `monitoring` folder (one level above the file of this function).
    If `config_file` is not absolute, it will be searched relatively to the `monitoring` folder as well.
    """
    config_file = config_file or "config.json"
    if not os.path.isabs(config_file):
        config_file = os.path.join(os.path.dirname(__file__), "..", config_file)
    
    with open(config_file, "r") as read_stream:
        config = json.load(read_stream)

    # Expand user directory in the ssh key, if present
    config["ssh_key_path"] = os.path.expanduser(config["ssh_key_path"])

    # Return config
    return config
