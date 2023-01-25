from monitoring.log_fetching.jobs.fetch_app_access_logs import FetchAppAccessLogs

job_list = {
    "app_access_logs": FetchAppAccessLogs,
    "app_event_logs": None,
    "database_scheduled_jobs_logs": None
}
