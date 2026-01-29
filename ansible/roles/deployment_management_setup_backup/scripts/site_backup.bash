# Wrapper over site backup script utility, called by current Ansible role

if [ ! -z "$BATS_TEST_DIRNAME" ]; then
    # If running tests
    PROJECT_ROOT="$(git -C "$BATS_TEST_DIRNAME" rev-parse --show-toplevel)"
else
    # If running a script on its own
    DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
fi

source "$PROJECT_ROOT/ansible/scripts/site_backup/main.bash"


# Set logging to file, if corresponding environment variables are provided
if [ ! -z "$BACKUP_LOG_FOLDER" ] && [ ! -z "$BACKUP_SCRIPT_LOG_FILENAME" ]; then
    LOG_MESSAGE_FILE="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
fi

if [ ! -z "$BACKUP_LOG_FILE_SEPARATOR" ]; then
    LOG_MESSAGE_SEP="$BACKUP_LOG_FILE_SEPARATOR"
fi


# Call site backup entrypoint with provided arguments
backup_main "$@"
