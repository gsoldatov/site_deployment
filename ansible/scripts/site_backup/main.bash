# Site backup script entry point

if [ ! -z "$BATS_TEST_DIRNAME" ]; then
    # If running tests
    PROJECT_ROOT="$(git -C "$BATS_TEST_DIRNAME" rev-parse --show-toplevel)"
else
    # If running a script on its own
    DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
fi

source "$PROJECT_ROOT/ansible/scripts/common/logging.bash"

source "$PROJECT_ROOT/ansible/scripts/site_backup/db.bash"
source "$PROJECT_ROOT/ansible/scripts/site_backup/static_files.bash"


: '
    Script for automatic site backup.

    Performs database & static files backup if corrsponding flags are provided
    and enough time since last backup has passed.
'
backup_main() {
    # Get script options & set paths
    local run_backup_db=0
    local run_backup_static_files=0

    while (( "$#" )); do    # Loop through input options, filter script options & save rest for Ansible
        case "$1" in
            --env-file) ENV_FILE=$2; shift; shift;;   # Relative to `<project_root>/ansible` folder

            --backup-db) run_backup_db=1; shift;;

            --backup-static-files) run_backup_static_files=1; shift;;

            *) shift;;
        esac
    done

    local env_file_fullpath="$PROJECT_ROOT/ansible/$ENV_FILE"

    # Read environment variables
    if [ -z "$ENV_FILE" ]; then echo 'Missing --env-file option, exiting.'; exit 1; fi
    if [[ ! -f $env_file_fullpath ]]; then echo "Env file '$env_file_fullpath' does not exist."; exit 1; fi

    source "$env_file_fullpath"
    log_message "DEBUG" "main" "Finished reading environment variables from '$env_file_fullpath'"

    # Run database backup
    if ((run_backup_db == 1)); then backup_db; fi

    # Run static files backup
    if ((run_backup_static_files == 1)); then backup_static_files; fi

    # Finish script exectuion
    log_message "INFO" "main" "Finished script execution."
}
