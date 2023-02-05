import os
from datetime import datetime

from monitoring.log_fetching.jobs.base_job import BaseJob
from monitoring.util.util import get_current_time


_DIGIT_CHARS = "0123456789."


class Healthcheck(BaseJob):
    def __init__(self, name, args, config, db_connection, log):
        super().__init__(name, args, config, db_connection, log)

        self.healthcheck_data = [
            get_current_time(),     # execution time
            False,      # server_reachable
            None,       # nginx_status
            None,       # backend_status
            None,       # db_status

            None,       # cpu_usage

            None,       # memory_used
            None,       # memory_available
            None,       # memory_swap
            None,       # memory_total

            None,       # disk_used
            None,       # disk_total
            None        # ssl_expiry_time
        ]
    

    def run_remote_commands(self):
        """ Get server healthcheck data. """
        # Nginx, backend and db status
        for i, service in [(2, "nginx"), (3, "site_backend"), (4, "postgresql")]:
            self.healthcheck_data[i] = self.ssh_connection.run(f"systemctl is-active {service}").stdout
        
        # CPU usage
        result = self.ssh_connection.run("top -b -n 1")
        for line in result.stdout.split("\n"):
            # Look for CPU line, e.g.:
            # %Cpu(s):  5.9 us,  5.9 sy,  0.0 ni, 88.2 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
            if line.find("Cpu") > -1:
                columns = line.split(",")
                idle_percentage = "".join((c for c in columns[3] if c in _DIGIT_CHARS))
                self.healthcheck_data[5] = 100 - float(idle_percentage)
                break
        
        # Memory
        result = self.ssh_connection.run("free | awk '$1 ~ \"Mem:\" { print $2, $3, $7 }'")  # total, used & available memory in KiB
        data = result.stdout.split(" ")
        self.healthcheck_data[6] = int(data[1])
        self.healthcheck_data[7] = int(data[2])
        self.healthcheck_data[9] = int(data[0])

        # Swap file size
        result = self.ssh_connection.run("free | awk '$1 ~ \"Swap:\" { print $2 }'")  # total swap file size in KiB
        self.healthcheck_data[8] = int(result.stdout)

        # Disk usage
        result = self.ssh_connection.run("df | awk '$NF ~ \"^/$\" { print $2, $3 }'")   # total & used number of 1 KiB blocks in the filesystem mounted on "/"
        data = result.stdout.split(" ")
        self.healthcheck_data[10] = int(data[1])
        self.healthcheck_data[11] = int(data[0])

        # SSL expiry time
        # get certificates' status | get info for server_domain (lines between Certificate name and ------ (not included))
        # | trim leading & trailing spaces | get expiry time
        cmd = f"certbot certificates | awk '/Certificate Name: {self.config['server_domain']}/" + "{flag=1}/- - - - - -/{flag=0}flag' " + \
            "| awk '{$1=$1};1' | awk '/Expiry Date/ { print $3, $4 }'"
        result = self.ssh_connection.sudo(cmd)
        self.healthcheck_data[12] = datetime.strptime(result.stdout.strip(), "%Y-%m-%d %H:%M:%S%z")    # "2021-01-01 12:34:56+00:00"


    def run(self):
        """ Ping server, get server healthcheck data and update the database. """
        # Ping server
        result = os.system(f"ping -c 1 -W 3 {self.config['server_addr']} > /dev/null")
        self.healthcheck_data[1] = result == 0

        if result != 0:
            self.log(self.name, "INFO", f"Server is unreachable.")
            self.update_data()
            return
        
        # Get and update healthcheck data
        self.connect_and_run_remote_commands()
        self.update_data()

        self.log(self.name, "INFO", "Successfully updated healthcheck data.")


    def update_data(self):
        """ Update healthcheck data in the database. """
        with self.db_connection:
            with self.db_connection.cursor() as cursor:
                cursor.execute("DELETE FROM healthcheck")

                query = "INSERT INTO healthcheck VALUES (" + ", ".join("%s" for _ in range(len(self.healthcheck_data))) + ")"
                cursor.execute(query, self.healthcheck_data)
