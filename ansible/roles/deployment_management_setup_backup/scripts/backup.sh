: "
    Script for automatic site backup.

    Performs database backup if it's enabled and enough time since last backup has passed.
"

# Source auxillary files
DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )    # Script directory
source $DIR/util.sh
source $DIR/backup_db.sh


# Get script options & set paths
while (( "$#" )); do    # Loop through input options, filter script options & save rest for Ansible
    case "$1" in
        --env-file) ENV_FILE=$2; shift; shift;;   # Relative to `ansible` folder (3 levels above script file location)

        *) shift;;
    esac
done

ENV_FILE_FULLPATH="$(dirname $(dirname $(dirname $DIR)))/$ENV_FILE"


# Read environment variables
if [ -z "$ENV_FILE" ]; then echo 'Missing --env-file option, exiting.'; exit 1; fi
if [[ ! -f $ENV_FILE_FULLPATH ]]; then echo "Env file '$ENV_FILE_FULLPATH' does not exist."; exit 1; fi

source $ENV_FILE_FULLPATH
log_message "DEBUG" "main" "Finished reading environment variables from '$ENV_FILE_FULLPATH'"

RUN_SH_FULLPATH="$LOCAL_SITE_FOLDER/deployment/ansible/run.sh"


# Run database backup
backup_db

# Finish script exectuion
log_message "INFO" "main" "Finished script execution."
