from datetime import datetime

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs


class FetchNginxAccessLogs(FetchRemoteLogs):
    def __init__(self, name, args, config, db_connection, log):
        remote_log_folder = config["fetched_logs_settings"]["nginx_log_folder"]
        filename_patterns = config["fetched_logs_settings"]["nginx_access_log_name_template"]
        
        separator = config["fetched_logs_settings"]["nginx_log_separator"]
        
        super().__init__(name, args, config, db_connection, log, remote_log_folder, filename_patterns, separator)

        self.timestamp_field_number = 3

        self.quote_open_close_chars = {'"': '"', '[': ']'}
    

    def get_line_fields(self, line):
        """
        Parses Nginx access log line in default (`combined`) formatting into a list of strings.

        `Combined` format:
        $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
        https://serverfault.com/questions/916653/what-is-the-default-log-format-on-nginx
        """
        fields = [""]
        current_quote_char = None

        for c in line:
            # If in inside quotes or brackets, ignore separator character
            if current_quote_char:
                # if quote_open_close_chars.get(c, None):
                if c == self.quote_open_close_chars[current_quote_char]:
                    current_quote_char = None
                else:
                    fields[-1] += c
            
            # If outside of quotes or brackets
            else:
                if c in self.quote_open_close_chars: 
                    current_quote_char = c
                elif c == self.separator:
                    fields.append("")
                elif c != "\n":
                    fields[-1] += c

        return fields
    

    def parse_timestamp(self, timestamp):
        """ Parses string `timestamp` in the Nginx's access log format. """
        return datetime.strptime(timestamp, "%d/%b/%Y:%H:%M:%S %z") # e.g.: "30/Jan/2023:00:54:38 +0300"

    
    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        request_fields = fields[4].split(" ")  # method, path, http version
        path = request_fields[1] if len(request_fields) > 1 else None
        method = None if len(request_fields[0]) > 8 else request_fields[0] if len(request_fields) > 1 else None

        return(
            AsIs("DEFAULT"),    # record_id
            self.parse_timestamp(fields[3]),    # record_time 
            path,     # path
            method,     # method
            int(fields[5]), # status
            int(fields[6]), # body_bytes_sent
            fields[0],  # remote
            None if fields[8] == "-" else fields[8], # user agent
            None if fields[7] == "-" else fields[7], # referer

            fields[4]   # request
        )
