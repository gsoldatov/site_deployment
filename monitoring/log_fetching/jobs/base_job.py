class BaseJob:
    """
    Base class for all jobs run by the log_fetching script.
    """
    def __init__(self, name, args, config, log):
        self.name = name
        self.args = args
        self.config = config
        self.log = log
    
    def run(self):
        """ Interface for executing a job. """
        raise NotImplementedError
