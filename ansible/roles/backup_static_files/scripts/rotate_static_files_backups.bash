 #!/bin/bash
# Rotates existing static files backup copies (script is executed before syncing files to a new backup)

if [ ! -z "$BATS_TEST_DIRNAME" ]; then
    # If running tests
    PROJECT_ROOT="$(git -C "$BATS_TEST_DIRNAME" rev-parse --show-toplevel)"
else
    # If running a script on its own
    DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
fi

source "$PROJECT_ROOT/ansible/scripts/common/rotate.bash"
source "$PROJECT_ROOT/ansible/scripts/common/util.bash"


# Set logging to file, if corresponding env variables are provided
if [ ! -z "$BACKUP_LOG_FOLDER" ] && [ ! -z "$BACKUP_LOGGING_STATIC_FILES_ROTATION_LOG_NAME" ]; then
    CURRENT_TIME=$(date "+%Y_%m_%d-%H_%M_%S")
    LOG_MESSAGE_FILE="$BACKUP_LOG_FOLDER/$BACKUP_LOGGING_STATIC_FILES_ROTATION_LOG_NAME""_$CURRENT_TIME.log"
fi

if [ ! -z "$BACKUP_LOG_FILE_SEPARATOR" ]; then
    LOG_MESSAGE_SEP="$BACKUP_LOG_FILE_SEPARATOR"
fi

log_message "INFO" "rotate_static_files_backups" "Starting static files backup rotation"

# Ensure environment variables are set
assert_variables "BACKUP_LOCAL_FOLDER" \
                 "BACKUP_STATIC_FILES_FOLDER_NAME" \
                 "BACKUP_STATIC_FILES_MAX_BACKUP_COUNT"

# Rotate database backups
rotate -p "$BACKUP_LOCAL_FOLDER" -f "$BACKUP_STATIC_FILES_FOLDER_NAME" -c "$BACKUP_STATIC_FILES_MAX_BACKUP_COUNT" -i 0

log_message "INFO" "rotate_static_files_backups" "Finished static files backup rotation"
