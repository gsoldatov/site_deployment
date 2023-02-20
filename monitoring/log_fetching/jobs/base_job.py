from fabric import Connection, Config
from invoke import Responder


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

        self.ssh_connection = None
    
    
    def run(self):
        """ Abstract method which is called to trigger job execution. """
        raise NotImplementedError
    

    def connect_and_run_remote_commands(self):
        """ Establish a temporary SSH connection to the server & run commands specified in `run_remote_commands` method. """
        try:
            config = Config(overrides={
                # Don't write command output in stdout & setup password for automatic sudo entering
                "run": {"hide": True},
                "sudo": {"password": self.config["server_user_password"], "hide": True}
            })
            # self.ssh_connection = Connection(
            self.ssh_connection = PatchedConnection(    # Used patched sudo method to allow calling it when running as a Cron job
                host=self.config["server_addr"],
                port=self.config["ssh_port"], 
                user=self.config["server_user"],
                connect_kwargs={ "key_filename": self.config["ssh_key_path"] },
                config=config
            )

            self.run_remote_commands()
        finally:
            # Close ssh connection
            if self.ssh_connection:
                if self.ssh_connection.is_connected:
                    self.ssh_connection.close()


    def run_remote_commands(self):
        """ Abstract method which should contain specific tasks to be run while connected to the server via SSH. """
        raise NotImplementedError


class PatchedConnection(Connection):
    def sudo(self, cmd, *args, **kwargs):
        """
        A workaround for avoiding `Socket is closed` error when Fabric's connection.sudo method.
        Error occures only for `sudo` (not `run`) method and when running as a Cron job (probably due do some shell environment difference).

        This method uses `run` method with auto response for password prompt, as suggested in docs (with a slight regex difference):
        https://docs.fabfile.org/en/stable/getting-started.html#superuser-privileges-via-auto-response

        Also, using this function requires a different approach in processing stdout, as it contains more text
        (password prompt + potentially, other lines).
        """
        sudopass = Responder(pattern=r"\[sudo\] password for", response=f'{self.config.sudo.password}\n')
        cmd = "sudo " + cmd

        return self.run(cmd, pty=True, watchers=[sudopass], *args, **kwargs)
