"""
Utility functions.
"""
from datetime import datetime


def get_local_tz():
    """ Returns datetime.timezone object corresponding to the timezone on the local machine. """
    return datetime.utcnow().astimezone().tzinfo


def get_current_time():
    """ Returns datetime object representing current time in the local timezone. """
    return datetime.now().replace(tzinfo=get_local_tz())