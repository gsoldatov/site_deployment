def get_logger():
    """
    Returns logging function (NOTE: currently supports stdout prints only).
    """
    def log(msg):
        print(msg)
    
    return log
