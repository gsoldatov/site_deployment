from monitoring.log_fetching.jobs.fetch_app_access_logs import FetchAppAccessLogs
from monitoring.log_fetching.jobs.fetch_app_event_logs import FetchAppEventLogs
from monitoring.log_fetching.jobs.fetch_database_scheduled_jobs_logs import FetchDatabaseScheduledJobsLogs
from monitoring.log_fetching.jobs.fetch_nginx_access_logs import FetchNginxAccessLogs
from monitoring.log_fetching.jobs.fetch_nginx_error_logs import FetchNginxErrorLogs
from monitoring.log_fetching.jobs.fetch_server_auth_logs import FetchServerAuthLogs
from monitoring.log_fetching.jobs.fetch_fail2ban_logs import FetchFail2banLogs
from monitoring.log_fetching.jobs.healthcheck import Healthcheck
from monitoring.log_fetching.jobs.fetch_backup_script_logs import FetchBackupScriptLogs

from monitoring.log_fetching.jobs.base_job import JobAborted


job_list = {
    "app_access_logs": FetchAppAccessLogs,
    "app_event_logs": FetchAppEventLogs,
    "database_scheduled_jobs_logs": FetchDatabaseScheduledJobsLogs,
    
    "nginx_access_logs": FetchNginxAccessLogs,
    "nginx_error_logs": FetchNginxErrorLogs,

    "server_auth_logs": FetchServerAuthLogs,
    "fail2ban_logs": FetchFail2banLogs,

    "healthcheck": Healthcheck,

    "backup_script_logs": FetchBackupScriptLogs
}
