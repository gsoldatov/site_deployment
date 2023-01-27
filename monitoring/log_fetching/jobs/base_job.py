class BaseJob:
    """
    Base class for all jobs run by the log_fetching script.
    """
    def __init__(self, name, args, config, db_connection, log):
        self.name = name
        self.args = args
        self.config = config
        self.db_connection = db_connection
        self.log = log
    
    def run(self):
        """ Interface for executing a job. """
        raise NotImplementedError
