# Utility functions for site backup

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


: '
    Echoes the timestamp of the last message matching a pattern
    provided as a positional argument from site backup script log files.

    If timestamp is not found, echoes 0.
'
get_last_log_message_time() {
    :
    # Ensure global variables are set
    assert_variables "BACKUP_LOG_FOLDER" \
                     "BACKUP_SCRIPT_LOG_FILENAME" \
                     "BACKUP_LOG_FILE_SEPARATOR"

    # Validate function arguments
    local pattern="$1"
    if [ -z "$pattern" ]; then
        log_message "ERROR" "get_last_log_message_time" "Missing required search pattern"
        exit 1
    fi
    
    # Find the latest log line, which matches search pattern, in the current file (file name is _____), using get_last_matching_line
    local log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"

    local line="$(get_last_matching_line "$log_file" "$pattern")"

    # If a line is found, get timestamp from it
    if [ ! -z "$line" ]; then
        mapfile -t line_elements < <(parse_log_message "$line" "$BACKUP_LOG_FILE_SEPARATOR")
        local timestamp="${line_elements[0]}"
        log_message "INFO" "get_last_log_message_time" "Found log message matching '$pattern' at $timestamp in the current file"
        echo "$(date -d "$timestamp" +%s)"
        return 0
    fi

    # Check first archived log file, if it exists
    local log_archive_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME.1.gz"
    if [ -f "$log_archive_file" ]; then
        # Create temp de-archived file in same directory
        local temp_log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME.temp"
        zcat "$log_archive_file" > "$temp_log_file" || {
            log_message "ERROR" "get_last_log_message_time" "Failed to dearchive $log_archive_file"
            exit 1
        }

        # Search in temporary log file and remove it
        local line="$(get_last_matching_line "$temp_log_file" "$pattern")"
        rm -f "$temp_log_file"

        # If a line is found, get timestamp from it
        if [ ! -z "$line" ]; then
            mapfile -t line_elements < <(parse_log_message "$line" "$BACKUP_LOG_FILE_SEPARATOR")
            local timestamp="${line_elements[0]}"
            log_message "INFO" "get_last_log_message_time" "Found log message matching '$pattern' at $timestamp in archived file"
            echo "$(date -d "$timestamp" +%s)"
            return 0
        fi
    fi

    # Return a default value, if timestamp is not found
    echo 0
}
