from datetime import datetime

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs


class FetchNginxErrorLogs(FetchRemoteLogs):
    def __init__(self, name, args, config, db_connection, log):
        remote_log_folder = config["fetched_logs_settings"]["nginx_log_folder"]
        filename_patterns = config["fetched_logs_settings"]["nginx_error_log_name_template"]
        
        separator = config["fetched_logs_settings"]["nginx_log_separator"]
        
        super().__init__(name, args, config, db_connection, log, remote_log_folder, filename_patterns, separator)


    def get_line_fields(self, line):
        """
        Parses an Nginx error log line into a list of strings.

        Line examples:
        2023/01/07 21:01:10 [error] 24209#24209: invalid PID number "" in "/run/nginx.pid"
        2023/01/10 09:21:46 [crit] 26071#26071: *1079 SSL_do_handshake() failed (SSL: error:1C800066:Provider routines::cipher operation failed error:0A000119:SSL routines::decryption failed or bad record mac) while SSL handshaking, client: 18.205.105.21, server: 0.0.0.0:443
        """
        fields = []
        l = line

        # Timestamp
        pos = l.find(" ")
        pos = l.find(" ", pos + 1)
        if pos == -1: raise ValueError(f"Failed to find timestamp's end in line:\n{line}")
        fields.append(l[:pos])

        # Level
        l = l[pos + 1:]
        pos = l.find(" ")
        if pos == -1: raise ValueError(f"Failed to find log level's end in line:\n{line}")
        fields.append(l[:pos])
        for c in ("[", "]"):
            fields[-1] = fields[-1].replace(c, "")
        
        # Message
        fields.append(l[pos + 1:])

        return fields
   

    def parse_timestamp(self, timestamp):
        """ Parses string `timestamp` in the Nginx's error log format. """
        return datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S").replace(tzinfo=self.server_timezone)    # e.g.: "2023/01/07 21:01:10"
    

    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        return (
            AsIs("DEFAULT"),    # record_id
            self.parse_timestamp(fields[0]),    # record_time 
            fields[1],  # level
            fields[2]   # message
        )
