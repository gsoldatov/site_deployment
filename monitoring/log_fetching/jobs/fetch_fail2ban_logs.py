from datetime import datetime

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs


class FetchFail2banLogs(FetchRemoteLogs):
    def __init__(self, name, args, config, db_connection, log):
        remote_log_folder = config["fetched_logs_settings"]["fail2ban_log_folder"]
        filename_patterns = config["fetched_logs_settings"]["fail2ban_log_name_template"]
        
        separator = " "
        
        super().__init__(name, args, config, db_connection, log, remote_log_folder, filename_patterns, separator)

        self.timestamp_field_number = 0
    

    def get_line_fields(self, line):
        """
        Parse fail2ban log line.

        Line examples:
        2023-01-29 13:14:46,577 fail2ban.actions        [2438]: NOTICE  [sshd] Ban 43.157.31.124
        2023-01-29 13:15:13,263 fail2ban.filter         [2438]: INFO    [sshd] Found 103.159.223.204 - 2023-01-29 13:15:13
        2023-01-29 13:16:59,366 fail2ban.actions        [2438]: NOTICE  [sshd] Unban 81.163.29.126
        """
        fields = []
        l = line

        # Timestamp
        pos = l.find(" ")
        pos = l.find(" ", pos + 1)
        if pos == -1: raise ValueError(f"Failed to find timestamp's end in line:\n{line}")
        fields.append(l[:pos])

        # Event type
        l = l[pos + 1:]
        pos = l.find(" ")
        if pos == -1: raise ValueError(f"Failed to find event type's end in line:\n{line}")
        fields.append(l[:pos])

        # Event level
        pos = l.find("[")
        if pos == -1: raise ValueError(f"Failed to event level's start in line:\n{line}")
        l = l[pos:]

        pos = l.find(" ")
        pos = l.find(" ", pos + 1)
        if pos == -1: raise ValueError(f"Failed to find event level's end in line:\n{line}")
        fields.append(l[:pos])
        l = l[pos:]

        # Jail or event source
        while len(l) > 0:
            if l[0] != " ": break
            l = l[1:]
        
        if len(l) == 0: raise ValueError(f"Failed to find jail start in line:\n{line}")
        
        if l[0] == "[":     # if jail in enclosed in brackets
            pos = l.find("]")
            if pos == -1: raise ValueError(f"Failed to find jail end bracket in line:\n{line}")
            fields.append(l[1:pos])
            pos += 2 # set starting position of message field
        else:    # jail is not enclosed in brackets
            pos = l.find(" ")
            # Some log lines don't have jail field, this is handled in the message section below
            # if pos == -1: raise ValueError(f"Failed to find jail end in line:\n{line}")
            fields.append(l[:pos])
            pos += 1 # set starting position of message field

        # Message
        if pos == 0:    # -1 + 1 for non bracketed jail field case means there was no jail field in the line, and jail column contains message
            fields.insert(3, None)
        else:   # jail field is not empty in the line
            fields.append(l[pos:])
            if fields[-1][-1] == "\n": fields[-1] = fields[-1].rstrip()     # Remove newline char at the end, if present

        return fields
    

    def parse_timestamp(self, timestamp):
        """ Parse string `timestamp` in the fail2ban log format and timezone to server local's. """
        # Add trailing zeroes to parse fraction part as microseconds
        timestamp += "000"
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=self.server_timezone) # e.g.: "2023-01-29 13:14:46,577"
    

    def filter_record(self, fields):
        """ Filter a record by its timestamp, jail and message. """
        # Timestamp
        if not super().filter_record(fields): return False

        # Jail
        if fields[3] != "sshd": return False

        # Message content (get only failed attempts & bans)
        for message_start in ("Ban", "Found"):
            if fields[4].startswith(message_start): return True
        
        return False

    
    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        message_parts = fields[4].split(" ")

        return (
            AsIs("DEFAULT"),    # record_id
            self.parse_timestamp(fields[0]),    # record_time 
            message_parts[0],   # event_type (ban or found [failed login])
            message_parts[1]    # remote
        )
