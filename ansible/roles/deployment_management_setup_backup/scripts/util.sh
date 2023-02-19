: "
    Utility functions.
"


: "
    Logging function for backup.sh script.
    Accepts 3 positional args: log level, message source and message.
"
log_message () {
    local TIMESTAMP=$(date "+%Y-%m-%dT%H:%M:%S %z")
    echo "$TIMESTAMP;$1;$2;$3" >> "$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
}


: "
    Checks if any of the active internet connections.
    Returns:
    - 0 if no active connections are metered, 1 if at least one active;
    - 1 if at least one active connection is metered;
    - 2 if there is no active connections.
"
is_metered_connection() {
    local ACTIVE_CONNECTIONS=$(nmcli -t -f NAME connection show --active)

    if [ -z $ACTIVE_CONNECTIONS ]; then return 2; fi
        
    for CONN in "$ACTIVE_CONNECTIONS"; do
        IS_METERED=$(nmcli -t -f connection.metered connection show $CONN | grep ':yes' | wc -l)
        if (( $IS_METERED == 1 )); then return 1; fi
    done

    return 0
}
