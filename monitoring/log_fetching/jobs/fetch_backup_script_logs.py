from datetime import datetime

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_local_logs import FetchLocalLogs


class FetchBackupScriptLogs(FetchLocalLogs):
    def __init__(self, name, args, config, db_connection, log):
        log_folder = config["fetched_logs_settings"]["backup_script_log_folder"]
        filename_pattern = config["fetched_logs_settings"]["backup_script_log_name_template"]
        
        separator = config["fetched_logs_settings"]["backup_script_separator"]
        
        super().__init__(name, args, config, db_connection, log, log_folder, filename_pattern, separator)


    def parse_timestamp(self, timestamp):
        """ Parse backup script timestamp. """
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S %z")   # e.g.: "2023-01-13T17:01:01 +0400"
    

    def transform_record(self, **kwargs):
        fields = kwargs["fields"]

        return(
            AsIs("DEFAULT"),    # record_id
            self.parse_timestamp(fields[0]),    # record_time
            fields[1],  # level
            fields[2],  # event_source
            fields[3]   # message
        )
