# ansisble/tasks/backup_db task tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'
    load '../../../test_helpers/util/parse_log_message'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "rotate_db_backups: run backup rotation script"
        "rotate_db_backups: file logging"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi

    script_path="$PROJECT_ROOT/ansible/roles/backup_db/scripts/rotate_db_backups.bash"
}


@test "rotate_db_backups: run backup rotation script" {
    # Missing environment variables
    run "$script_path"
    assert_equal $status 1
    assert_output --partial "Variable 'BACKUP_LOCAL_FOLDER' is not defined or empty"

    export BACKUP_LOCAL_FOLDER="$TEST_CASE_TEMP_DIR"
    run "$script_path"
    assert_equal $status 1
    assert_output --partial "Variable 'BACKUP_DB_DUMP_FILENAME' is not defined or empty"
    
    export BACKUP_DB_DUMP_FILENAME="mock_backup.tar"
    run "$script_path"
    assert_equal $status 1
    assert_output --partial "Variable 'BACKUP_DB_MAX_BACKUP_COUNT' is not defined or empty"
    
    # Add mock backups
    export BACKUP_DB_MAX_BACKUP_COUNT=5
    echo "v0" > "$TEST_CASE_TEMP_DIR/$BACKUP_DB_DUMP_FILENAME"
    echo "v1" > "$TEST_CASE_TEMP_DIR/$BACKUP_DB_DUMP_FILENAME.1"

    # Successfully rotate mock backups
    run "$script_path"
    assert_success
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/$BACKUP_DB_DUMP_FILENAME")" = "v0" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/$BACKUP_DB_DUMP_FILENAME.1")" = "v0" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/$BACKUP_DB_DUMP_FILENAME.2")" = "v1" ]
}


@test "rotate_db_backups: file logging" {
    # Set required environment variables
    export BACKUP_LOCAL_FOLDER="$TEST_CASE_TEMP_DIR"
    export BACKUP_DB_DUMP_FILENAME="mock_backup.tar"
    export BACKUP_DB_MAX_BACKUP_COUNT=5

    # Add a mock backup file
    echo "v0" > "$TEST_CASE_TEMP_DIR/$BACKUP_DB_DUMP_FILENAME"

    # Set logging environment variables
    export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
    export BACKUP_LOGGING_DB_ROTATION_LOG_FILENAME="rotation.log"
    export BACKUP_LOG_FILE_SEPARATOR="|"

    # Run db backup rotation
    run "$script_path"
    assert_success

    # Check if log messages were written to the expected file
    local log_filename=$(find "$BACKUP_LOG_FOLDER" -type f -name "$BACKUP_LOGGING_DB_ROTATION_LOG_FILENAME*" | head -n 1)
    mapfile -t lines < <(tail -n 1 "$log_filename")  # read file lines to array
    parse_log_message "${lines[0]}" "$BACKUP_LOG_FILE_SEPARATOR"
    assert_equal "${log_message_elements[1]}" "INFO"
    assert_equal "${log_message_elements[2]}" "rotate_db_backups"
    assert_equal "${log_message_elements[3]}" "Finished db backup rotation"
}
