from dotenv import dotenv_values
from pathlib import Path


def get_config(env_file = None):
    """
    Returns a dict with monitoring configuration based on the contents of the provided `env_file`.
    `env_file` can be absolute or relative to `ansible` directory of the project (defaults to `production.env` in that directory).
    """
    env_file = env_file or "production.env"
    path = Path(env_file)
    if not path.is_absolute():
        path = Path(__file__).parent.parent.parent / "ansible" / path
    
    env_vars = dotenv_values(path)

    return _get_monitoring_config(env_vars)


def _get_monitoring_config(env_vars):
    # Remove prefix from domain
    server_domain = env_vars["SERVER_URLS"].split(" ")[0].replace("https://", "")

    # Expand user directory in the ssh key, if present;
    # convert expanded path to string (expected by paramiko SSHClient)
    ssh_key_path = str(Path(env_vars["DEPLOYMENT_USER_KEY_PATH"]).expanduser())

    backend_log_folder = str(Path(env_vars["SERVER_BACKEND_FOLDER"]) / "logs")

    backup_log_name_template = env_vars["BACKUP_SCRIPT_LOG_FILENAME"] + "*"
    

    return {
        "server_addr": env_vars["SERVER_ADDR"],
        "server_domain": server_domain,
        "ssh_port": 22,
        "server_user": env_vars["DEPLOYMENT_USER_NAME"],
        "server_user_password": env_vars["DEPLOYMENT_USER_PASSWORD"],
        "ssh_key_path": ssh_key_path,

        "db": {
            "db_host": "localhost",
            "db_port": 5432,
            
            "db_init_database": env_vars["MONITORING_INIT_DB_NAME"],
            "db_init_username": env_vars["MONITORING_INIT_DB_USERNAME"],
            "db_init_password": env_vars["MONITORING_INIT_DB_PASSWORD"],
            
            "db_database": env_vars["MONITORING_DB_NAME"],
            "db_username": env_vars["MONITORING_DB_USERNAME"],
            "db_password": env_vars["MONITORING_DB_PASSWORD"],
        },

        "local_temp_folder": "temp",
        "logging_mode": "db",

        "fetched_logs_settings": {
            "remote_temp_folder": env_vars["REMOTE_TEMP_FOLDER"],

            "backend_log_folder": backend_log_folder,
            "backend_log_separator": env_vars["BACKEND_SETTING_LOGGING_FILE_SEPARATOR"],
            "app_access_log_name_template": "app_access_log*",
            "app_event_log_name_template": "app_event_log*",
            "database_scheduled_jobs_log_name_templates": ["clear_expired_login_limits*", "clear_expired_sessions*", "update_searchables*"],

            "nginx_log_folder": "/var/log/nginx",
            "nginx_access_log_name_template": "access.log*",
            "nginx_error_log_name_template": "error.log*",
            "nginx_log_separator": " ",

            "fail2ban_log_folder": "/var/log",
            "fail2ban_log_name_template": "fail2ban.log*",

            "backup_script_log_folder": env_vars["BACKUP_LOG_FOLDER"],
            "backup_script_log_name_template": backup_log_name_template,
            "backup_script_separator": ";"
        }
    }
