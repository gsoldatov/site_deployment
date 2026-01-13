 #!/bin/bash
# Rotates existing database backup copies (script is executed before fetching a new backup)

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


# Ensure environment variables are set
assert_variables "BACKUP_LOCAL_FOLDER" "BACKUP_DB_DUMP_FILENAME" "BACKUP_DB_MAX_BACKUP_COUNT"

# Rotate database backups
rotate -p "$BACKUP_LOCAL_FOLDER" -f "$BACKUP_DB_DUMP_FILENAME" -c "$BACKUP_DB_MAX_BACKUP_COUNT" -i 0
