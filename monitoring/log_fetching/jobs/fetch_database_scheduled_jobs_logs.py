import os

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.fetch_remote_logs import FetchRemoteLogs


_job_types = ("clear_expired_login_limits", "clear_expired_sessions", "update_searchables")


class FetchDatabaseScheduledJobsLogs(FetchRemoteLogs):
    def __init__(self, name, args, config, db_connection, log):
        remote_log_folder = config["fetched_logs_settings"]["backend_log_folder"]
        filename_patterns = config["fetched_logs_settings"]["database_scheduled_jobs_log_name_templates"]
        
        separator = config["fetched_logs_settings"]["backend_log_separator"]
        
        super().__init__(name, args, config, db_connection, log, remote_log_folder, filename_patterns, separator)
    

    def transform_line(self, **kwargs):
        fields = kwargs["line"].split(self.separator)
        
        filename = os.path.basename(kwargs["file"])
        job_type = None
        for jt in _job_types:
            if filename.startswith(jt):
                job_type = jt
                break
        if not job_type:
            raise ValueError(f"Received an unexpected filename: '{filename}'.")

        return (
            AsIs("DEFAULT"), # record_id
            job_type,       # job_type
            self.parse_timestamp(fields[0]),    # record_time
            fields[1],  # level
            fields[2]   # message
        )
