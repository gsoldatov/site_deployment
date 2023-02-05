from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs


class FetchAppEventLogs(FetchRemoteLogs):
    def __init__(self, name, args, config, db_connection, log):
        log_folder = config["fetched_logs_settings"]["backend_log_folder"]
        filename_patterns = config["fetched_logs_settings"]["app_event_log_name_template"]
        
        separator = config["fetched_logs_settings"]["backend_log_separator"]
        
        super().__init__(name, args, config, db_connection, log, log_folder, filename_patterns, separator)
    

    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        return (
            AsIs("DEFAULT"), # record_id
            self.parse_timestamp(fields[0]),    # record_time
            fields[1],      # request_id
            fields[2],      # level
            fields[3] or None,      # event_type
            fields[4] or None,      # message
            fields[5] or None       # details
        )
