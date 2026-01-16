: "
    Function for automatic database backup
"
backup_db () {
    # Exit if database backup is diabled
    if (($BACKUP_DB_MAX_BACKUP_COUNT <= 0)); then log_message "INFO" "backup_db" "Database backup is disabled."; return 0; fi

    # Exit if not enough time since last backup has passed
    if [[ -f "$BACKUP_LOCAL_FOLDER/$BACKUP_DB_DUMP_FILENAME" ]]; then
        CURRENT_TIME=$(date +%s)
        FILE_MODIFY_TIME=$(date -r "$BACKUP_LOCAL_FOLDER/$BACKUP_DB_DUMP_FILENAME" +%s)
        if (( $CURRENT_TIME - $FILE_MODIFY_TIME < $BACKUP_DB_MIN_INTERVAL * 60 )); then 
            log_message "INFO" "backup_db" "Existing backup with recent modify time found, exiting."
            return 0
        fi
    fi

    # Check if internet connection is metered
    is_metered_connection
    local CONN_STATUS=$?
    if (($CONN_STATUS == 2)); then log_message "INFO" "backup_db" "No internet connection available."; return 0; fi
    if (($CONN_STATUS == 1)); then log_message "INFO" "backup_db" "Internet connection is metered, exiting."; return 0; fi

    # Check if server is reachable
    ping -c1 $SERVER_ADDR > /dev/null 2>&1
    if (($? > 0)); then
        log_message "INFO" "backup_db" "Production server is currently unreachable."
        return 0
    fi

    # Run database backup
    local CURRENT_TIME=$(date "+%Y_%m_%d-%H_%M_%S")
    local PLAYBOOK_LOG_FULLPATH="$BACKUP_LOG_FOLDER/$BACKUP_LOGGING_DB_ANSIBLE_LOG_FILENAME""_$CURRENT_TIME.log"
    PLAYBOOK_LOG=$(bash $RUN_SH_FULLPATH backup_execute.yml --tags "backup_db" --env-file "$ENV_FILE"; exit $?;)
    local EXIT_CODE=$?
    echo "$PLAYBOOK_LOG" > $PLAYBOOK_LOG_FULLPATH

    if (($EXIT_CODE > 0)); then 
        log_message "ERROR" "backup_db" "Database backup execution finished with a non-zero exit code, see $PLAYBOOK_LOG_FULLPATH"
    else
        log_message "INFO" "backup_db" "Finished database backup."
    fi
}
