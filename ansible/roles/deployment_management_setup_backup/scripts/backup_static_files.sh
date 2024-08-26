: "
    Function for automatic static files backup
"
backup_static_files () {
    # Exit if static files backup is diabled
    if (($BACKUP_STATIC_FILES_MAX_BACKUP_COUNT <= 0)); then log_message "INFO" "backup_static_files" "Static files backup is disabled."; return 0; fi

    # Check if internet connection is metered
    is_metered_connection
    local CONN_STATUS=$?
    if (($CONN_STATUS == 2)); then log_message "INFO" "backup_static_files" "No internet connection available."; return 0; fi
    if (($CONN_STATUS == 1)); then log_message "INFO" "backup_static_files" "Internet connection is metered, exiting."; return 0; fi

    # Check if server is reachable
    ping -c1 $SERVER_ADDR > /dev/null 2>&1
    if (($? > 0)); then
        log_message "INFO" "backup_static_files" "Production server is currently unreachable."
        return 0
    fi

    # Run static files backup
    local CURRENT_TIME=$(date "+%Y_%m_%d-%H_%M_%S")
    local PLAYBOOK_LOG_FULLPATH="$BACKUP_LOG_FOLDER/$BACKUP_STATIC_FILES_ANSIBLE_LOG_FILENAME""_$CURRENT_TIME.log"
    PLAYBOOK_LOG=$(bash $RUN_SH_FULLPATH backup_execute.yml --tags "backup_static_files" --env-file "$ENV_FILE"; exit $?;)
    local EXIT_CODE=$?
    echo "$PLAYBOOK_LOG" > $PLAYBOOK_LOG_FULLPATH

    if (($EXIT_CODE > 0)); then 
        log_message "ERROR" "backup_static_files" "Static files backup execution finished with a non-zero exit code, see $PLAYBOOK_LOG_FULLPATH"
    else
        log_message "INFO" "backup_static_files" "Finished static files backup."
    fi
}
