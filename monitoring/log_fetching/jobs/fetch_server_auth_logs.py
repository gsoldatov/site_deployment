import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs
from monitoring.util.util import get_current_time, get_local_tz


class FetchServerAuthLogs(FetchRemoteLogs):
    """
    Dumps and saves login data from wtmp files. Updates list of known ips in the database.

    NOTE: for more info about wtmp files, see:
    https://unix.stackexchange.com/questions/126166/how-to-interpret-all-fields-of-utmpdump-var-log-utmp (log field descriptions)
    https://www.linkedin.com/pulse/using-linux-utmpdump-forensics-detecting-log-file-craig-rowland (ut_type description & notes on security)
    """
    def __init__(self, name, args, config, db_connection, log):
        log_folder = config["fetched_logs_settings"]["server_auth_temp_folder_name_template"] + f"_{str(uuid4())[:8]}"
        filename_patterns = "wtmp*"
        
        separator = " "
        
        super().__init__(name, args, config, db_connection, log, log_folder, filename_patterns, separator)

        self.timestamp_field_number = 7
        self.current_ip_address = None
    

    def run_remote_commands(self):
        """ Get ip address of the current SSH connection, then fetch files. """
        result = self.ssh_connection.run("echo $SSH_CLIENT | awk '{ print $1}'")
        self.current_ip_address = result.stdout.strip()
        super().run_remote_commands()
    

    def fetch_files(self):
        """ Search for wtmp files and dumps them into temp folder, then fetches as regular log files. """
        # Get matching wtmp files
        wtmp_folder = "/var/log"
        cmd = f'find "{wtmp_folder}" -mindepth 1 -name "{self.filename_patterns}"'
        if not self.full_fetch:  # Filter files by time if not running full fetch
            t = self.min_time.isoformat()
            cmd +=  f' -newermt "{t}"'
        result = self.ssh_connection.sudo(cmd)

        # Exit if no matching files found
        self.number_of_matching_files = len(result.stdout.strip())
        if self.number_of_matching_files == 0:
            self.log(self.name, "INFO", "Found no matching files.")
            return
        
        wtmp_files = result.stdout.strip().split("\n")

        try:
            # Dump wtmp files into temp folder
            self.ssh_connection.sudo(f'mkdir "{self.log_folder}"')
            # Output redirect is performed by current user instead of root, even when running as sudo, so folder ownership must be updated
            self.ssh_connection.sudo(f'chown -R {self.config["server_user"]} "{self.log_folder}"')
            for file in wtmp_files:
                temp_filename = os.path.join(self.log_folder, os.path.basename(file))
                self.ssh_connection.sudo(f"utmpdump {file} > '{temp_filename}'")
            
            # Fetch dumps as regular log files
            super().fetch_files()
        
        finally:
            # Remove temp folder & wtmp dumps
            self.ssh_connection.sudo(f"rm -rf '{self.log_folder}'")
    

    def get_line_fields(self, line):
        """
        Parse a wtmp dump log line into a list of strings.

        Line examples:
        [7] [01517] [ts/0] [root    ] [pts/0       ] [8.8.8.8      ] [8.8.8.8 ] [2023-01-07T17:08:08,758217+00:00]
        [8] [00954] [    ] [        ] [pts/0       ] [                    ] [0.0.0.0        ] [2023-01-07T17:08:08,945060+00:00]
        """
        fields = [""]
        is_inside_brackets = False

        for c in line:
            # If in inside quotes or brackets, ignore separator character
            if is_inside_brackets:
                if c == "]":
                    is_inside_brackets = False
                else:
                    fields[-1] += c
            
            # If outside of  brackets
            else:
                if c == "[": 
                    is_inside_brackets = True
                elif c == self.separator:
                    fields.append("")
                elif c != "\n":
                    fields[-1] += c

        return fields
   

    def parse_timestamp(self, timestamp):
        """ Parse string `timestamp` in the wtmp dump format. """
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S,%f%z")
        # return datetime.fromisoformat(timestamp)
    

    def filter_record(self, fields):
        """ Filter by timestamp and ut_type value. """
        # Filter by timestamp
        if not super().filter_record(fields): return False

        # Filter by ut_type value:
        # - 7 - user process (ssh login);
        # - 0 - missing data.
        # See `man 5 utmp` for more info.
        return fields[0] in ("7", "0")
    

    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        # Ensure all timestamps are in the local timezone, 
        # so that they can be correctly compared to `login_date` of `known_ips` table
        # (which is derived from this value and contains its date, as in the timezone record_time is converted to)
        # e.g.: 
        # log line timestamp = '2022-12-31 23:00:00 +0000'
        # record_time = '2023-01-01 02:00:00 +0300', where '+0300' is local timezone
        # login_date = '2023-01-01'
        # NOTE: login_date must always represent date in the local timezone, because
        # `server_auth_logs.record_time::DATE` SQL statement will return the date in the local timezone as well.
        record_time = self.parse_timestamp(fields[7]).astimezone(get_local_tz())

        user = fields[3].strip()
        if len(user) == 0: user = None

        remote = fields[6].strip()
        if len(remote) == 0: remote = None

        return (
            AsIs("DEFAULT"),    # record_id
            record_time,
            int(fields[0]),  # ut_type
            user,
            remote
        )
    

    def insert_data(self, data, cursor):
        """ Insert matching records via default insert method, then insert current ip into `known_ips`. """
        super().insert_data(data, cursor)

        login_date = get_current_time().date()
        cursor.execute("""
            INSERT INTO known_ips VALUES (DEFAULT, %s, %s) ON CONFLICT DO NOTHING
        """, [login_date, self.current_ip_address])
