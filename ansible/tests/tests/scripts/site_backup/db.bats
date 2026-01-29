# ansisble/scripts/site_backup/db.bash module tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'

    load '../../../../scripts/site_backup/db'

    # Create a temporary directory for each test case
    ensure_test_case_subdir

    # Export required global variables
    test_cases_without_preset_variables=(
       "backup_db: required global variables"
    )

    if ! printf '%s\n' "${test_cases_without_preset_variables[@]}" | grep -Fxq -- "$BATS_TEST_DESCRIPTION"; then
        export BACKUP_DB_MAX_BACKUP_COUNT=10
        export BACKUP_DB_MIN_INTERVAL=60
        export SERVER_ADDR="127.0.0.1"
        export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
        export BACKUP_LOGGING_DB_ANSIBLE_LOG_FILENAME="backup_db_ansible.log"
        export ENV_FILE="some_file.env"
    fi

    # Export global variables for last backup execution time check
    # export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
    export BACKUP_SCRIPT_LOG_FILENAME="backup.log"
    export BACKUP_LOG_FILE_SEPARATOR=";"

    # Set default mocks for supplementary functions
    is_metered_connection() { return 0; }
    ping() { return 0; }
    
    # Set a default mock db backup execution via Ansible
    load '../../../test_helpers/mocks/site_backup/db_backup.bash'
}


@test "backup_db: required global variables" {
    run backup_db
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_DB_MAX_BACKUP_COUNT' is not defined or empty"

    export BACKUP_DB_MAX_BACKUP_COUNT=10
    run backup_db
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_DB_MIN_INTERVAL' is not defined or empty"

    export BACKUP_DB_MIN_INTERVAL=60
    run backup_db
    assert_failure 1
    assert_output --partial "Variable 'SERVER_ADDR' is not defined or empty"

    export SERVER_ADDR="127.0.0.1"
    run backup_db
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_LOG_FOLDER' is not defined or empty"

    export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
    run backup_db
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_LOGGING_DB_ANSIBLE_LOG_FILENAME' is not defined or empty"

    export BACKUP_LOGGING_DB_ANSIBLE_LOG_FILENAME="backup_db_ansible.log"
    run backup_db
    assert_failure 1
    assert_output --partial "Variable 'ENV_FILE' is not defined or empty"

    # Check if backup was not triggered
    [ ! -f "$BACKUP_DB_RUN_FILE" ]
}


@test "backup_db: backup is disabled" {
    export BACKUP_DB_MAX_BACKUP_COUNT=0

    # Check if backup was not triggered
    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Database backup is disabled."
    [ ! -f "$BACKUP_DB_RUN_FILE" ]
}


@test "backup_db: backup was performed recently" {
    # Write a log line indicating recent backup
    local log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
    local current_time=$(date +%s)
    local last_backup_timestamp=$((current_time - 60 * 60 + 2)) # add 2 seconds to avoind flaky execution
    local last_backup_datetime=$(date -d "@$last_backup_timestamp" "$LOG_TIMESTAMP_FORMAT")

    echo "$last_backup_datetime;INFO;backup_db;Finished database backup." >> "$log_file"

    # Check if backup was not triggered
    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Database backup was performed recently, exiting."
    [ ! -f "$BACKUP_DB_RUN_FILE" ]
}


@test "backup_db: no Internet & metered connection" {
    # No internet connection
    is_metered_connection() { return 2; }

    run backup_db
    assert_success
    assert_output --regexp "backup_db.*No internet connection available."
    [ ! -f "$BACKUP_DB_RUN_FILE" ]

    # Metered Internet connection
    is_metered_connection() { return 1; }

    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Internet connection is metered, exiting."
    [ ! -f "$BACKUP_DB_RUN_FILE" ]
}


@test "backup_db: ping & server is unreachable" {
    # Override default ping mock with a failing version
    ping() {
        assert_equal "$1" "-c1"
        assert_equal "$2" "$SERVER_ADDR"
        return 1
    }

    # Check if backup was not triggered
    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Production server is currently unreachable."
    [ ! -f "$BACKUP_DB_RUN_FILE" ]
}


@test "backup_db: backup command failed" {
    # Override the default mock for backup via Ansible with a failing version
    load '../../../test_helpers/mocks/site_backup/db_backup_failing.bash'

    # Check if backup was triggered, but failed
    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Database backup execution finished with a non-zero exit code"
    [ -f "$BACKUP_DB_RUN_FILE" ]
    assert_equal "$(cat "$BACKUP_DB_RUN_FILE")" "triggered failing backup"
}


@test "backup_db: successful run without logs" {
    # Run a successful backup
    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Finished database backup."
    [ -f "$BACKUP_DB_RUN_FILE" ]
    assert_equal "$(cat "$BACKUP_DB_RUN_FILE")" "triggered successful backup"
}


@test "backup_db: successful run with logs" {
    # Write a log line indicating a non-recent backup
    local log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
    local current_time=$(date +%s)
    local last_backup_timestamp=$((current_time - 60 * 60 - 1))
    local last_backup_datetime=$(date -d "@$last_backup_timestamp" "$LOG_TIMESTAMP_FORMAT")

    echo "$last_backup_datetime;INFO;backup_db;Finished database backup." >> "$log_file"

    # Check if backup was triggered
    run backup_db
    assert_success
    assert_output --regexp "backup_db.*Finished database backup."
    [ -f "$BACKUP_DB_RUN_FILE" ]
    assert_equal "$(cat "$BACKUP_DB_RUN_FILE")" "triggered successful backup"
}
