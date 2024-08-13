from functools import wraps
import traceback

from fabric import Connection, Config
from invoke import Responder
from paramiko.ssh_exception import SSHException, NoValidConnectionsError


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
                config=config,

                # Custom args used during exception handling
                job_name=self.name,
                job_logger=self.log
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
    def __init__(self, *args, **kwargs):
        job_name, job_logger = kwargs.pop("job_name"), kwargs.pop("job_logger")
        super().__init__(*args, **kwargs)

        # Decorate `run` method with exception catching function
        exception_handler_decorator = handle_ssh_errors(job_name, job_logger)
        self.run = exception_handler_decorator(self.run)

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


def handle_ssh_errors(job_name, job_logger):
    """
    Catches various SSH & connection errors during command execution via SSH.
    Logs caught errors with `job_logger` function (`log` method of the BaseJob instance), writing the provided `job_name`,
    and raises `JobAborted` exception instead, which is handled by the job runner.
    `log` should be set to `log` method of `BaseJob` instance, which creates an instance of this class.
    """
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            # Higher-level errors from Fabric's dependencies
            except (SSHException, NoValidConnectionsError, EOFError):
                job_logger(job_name, "WARNING", f"Failed to execute a command over SSH\n\n{traceback.format_exc()}")
                raise JobAborted

            # Low-level socket errors
            except OSError as e:
                # Errno 110 appears in TimeoutError instances, which are subclasses of OSError
                for msg in ("[Errno 101] Network is unreachable", "[Errno 110] Connection timed out"):
                    if msg in str(e):
                        job_logger(job_name, "WARNING", f"Failed to execute a command over SSH\n\n{traceback.format_exc()}")
                        raise JobAborted
                raise

        return inner
    return outer


class JobAborted(Exception):
    pass