# Site static files backup logic

if [ ! -z "$BATS_TEST_DIRNAME" ]; then
    # If running tests
    PROJECT_ROOT="$(git -C "$BATS_TEST_DIRNAME" rev-parse --show-toplevel)"
else
    # If running a script on its own
    DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
fi

source "$PROJECT_ROOT/ansible/scripts/common/logging.bash"
source "$PROJECT_ROOT/ansible/scripts/common/util.bash"
source "$PROJECT_ROOT/ansible/scripts/site_backup/util.bash"


: '
    Runs Ansible playbook, which rotates existing static files backups
    and makes a new one, after a specified interval has passed
'
backup_static_files () {
    log_message "INFO" "backup_static_files" "Started static files backup."

    # Validate required global variables
    assert_variables "BACKUP_STATIC_FILES_MAX_BACKUP_COUNT" \
                     "BACKUP_STATIC_FILES_MIN_INTERVAL" \
                     "SERVER_ADDR" \
                     "BACKUP_LOG_FOLDER" \
                     "BACKUP_LOGGING_STATIC_FILES_ANSIBLE_LOG_FILENAME" \
                     "ENV_FILE"
    
    # Exit if static files backup is diabled
    if (($BACKUP_STATIC_FILES_MAX_BACKUP_COUNT <= 0));
        then log_message "INFO" "backup_static_files" "Static files backup is disabled."
        return 0
    fi

    # Exit, if not enough time since last backup has passed
    local last_backup_time=$(get_last_log_message_time "Finished static files backup.")
    local current_time=$(date +%s)
    if (( $current_time - $last_backup_time < $BACKUP_STATIC_FILES_MIN_INTERVAL * 60 )); then 
        log_message "INFO" "backup_static_files" "Static files backup was performed recently, exiting."
        return 0
    fi

    # Check if internet connection is metered
    is_metered_connection
    local conn_status=$?
    if (($conn_status == 2)); then log_message "INFO" "backup_static_files" "No internet connection available."; return 0; fi
    if (($conn_status == 1)); then log_message "INFO" "backup_static_files" "Internet connection is metered, exiting."; return 0; fi

    # Check if server is reachable
    ping -c1 $SERVER_ADDR > /dev/null 2>&1
    if (($? > 0)); then
        log_message "INFO" "backup_static_files" "Production server is currently unreachable."
        return 0
    fi

    # Run static files backup
    local current_time=$(date "+%Y_%m_%d-%H_%M_%S")
    local playbook_log_file_path="$BACKUP_LOG_FOLDER/$BACKUP_LOGGING_STATIC_FILES_ANSIBLE_LOG_FILENAME""_$current_time.log"
    (eval "$RUN_STATIC_FILES_BACKUP_COMMAND") > "$playbook_log_file_path"     # use a subshell to enable passing status code from ansible
    local playbook_exit_code=$?

    if (($playbook_exit_code > 0)); then 
        log_message "ERROR" "backup_static_files" "Static files backup execution finished with a non-zero exit code, see $playbook_log_file_path"
    else
        log_message "INFO" "backup_static_files" "Finished static files backup."
    fi
}

# Moved outside of main function for the sake of mockability
# (don't override mock variable, if it's set)
if [ -z "$RUN_STATIC_FILES_BACKUP_COMMAND" ]; then
    RUN_STATIC_FILES_BACKUP_COMMAND='bash "$PROJECT_ROOT/ansible/run.sh" backup_execute.yml --tags "backup_static_files" --env-file "$ENV_FILE"; exit $?;'
fi
