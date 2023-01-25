"""
Utility functions.
"""
import os
import subprocess
from datetime import datetime


def check_internet_connection(force, log):
    """
    Checks existing internet connection via .sh function and exits if it's unavailable or metered.
    If `force` is set to True, ignores metered connection.
    """
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ansible/roles/backup_schedule/scripts/util.sh"))
    cmd = f"bash -c \"source '{script_path}'; is_metered_connection\"" # bash interpreter is required to correctly source the function
                                                                       # subprocess uses /bin/sh, which may be linked to dash
    proc = subprocess.Popen(cmd, shell=True)
    proc.communicate()

    if proc.returncode == 2: log("No internet connection available."); exit(2)
    elif proc.returncode == 1 and not force: log("Internet connection is metered."); exit(1)


def get_local_tz():
    """ Returns datetime.timezone object corresponding to the timezone on the local machine. """
    return datetime.utcnow().astimezone().tzinfo