from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs


class FetchAppAccessLogs(FetchRemoteLogs):
    def __init__(self, name, args, config, db_connection, log):
        log_folder = config["fetched_logs_settings"]["backend_log_folder"]
        filename_patterns = config["fetched_logs_settings"]["app_access_log_name_template"]
        
        separator = config["fetched_logs_settings"]["backend_log_separator"]
        
        super().__init__(name, args, config, db_connection, log, log_folder, filename_patterns, separator)
    

    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        return (
            AsIs("DEFAULT"), # record_id
            self.parse_timestamp(fields[0]),    # record_time
            fields[1],      # request_id
            fields[2],      # path
            fields[3],      # method
            int(fields[4]), # status
            fields[5],      # elapsed_time
            None if fields[6] == "anonymous" else int(fields[6]),   # user_id
            fields[7],      # remote
            fields[8],      # user agent
            fields[9]       # referer
        )
    