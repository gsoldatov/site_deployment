# ansisble/tasks/backup_db task tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'
    load '../../../../scripts/common/logging'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "rotate_static_files_backups: run backup rotation script"
        "rotate_static_files_backups: file logging"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi

    script_path="$PROJECT_ROOT/ansible/roles/backup_static_files/scripts/rotate_static_files_backups.bash"
}


@test "rotate_static_files_backups: run backup rotation script" {
    # Missing environment variables
    run "$script_path"
    assert_equal $status 1
    assert_output --partial "Variable 'BACKUP_LOCAL_FOLDER' is not defined or empty"

    export BACKUP_LOCAL_FOLDER="$TEST_CASE_TEMP_DIR"
    run "$script_path"
    assert_equal $status 1
    assert_output --partial "Variable 'BACKUP_STATIC_FILES_FOLDER_NAME' is not defined or empty"
    
    export BACKUP_STATIC_FILES_FOLDER_NAME="static_files"
    run "$script_path"
    assert_equal $status 1
    assert_output --partial "Variable 'BACKUP_STATIC_FILES_MAX_BACKUP_COUNT' is not defined or empty"
    
    # Add mock backups
    export BACKUP_STATIC_FILES_MAX_BACKUP_COUNT=5
    mkdir "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME"
    touch "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME/a"
    mkdir "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME.1"
    touch "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME.1/b"

    # Successfully rotate mock backups
    run "$script_path"
    assert_success
    assert [ -f "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME/a" ]
    assert [ -f "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME.1/a" ]
    assert [ -f "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME.2/b" ]
}


@test "rotate_static_files_backups: file logging" {
    # Set required environment variables
    export BACKUP_LOCAL_FOLDER="$TEST_CASE_TEMP_DIR"
    export BACKUP_STATIC_FILES_FOLDER_NAME="static_files"
    export BACKUP_STATIC_FILES_MAX_BACKUP_COUNT=5

    # Add a mock backup
    mkdir "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME"
    touch "$TEST_CASE_TEMP_DIR/$BACKUP_STATIC_FILES_FOLDER_NAME/a"

    # Set logging environment variables
    export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
    export BACKUP_LOGGING_STATIC_FILES_ROTATION_LOG_FILENAME="rotation.log"
    export BACKUP_LOG_FILE_SEPARATOR="|"

    # Run db backup rotation
    run "$script_path"
    assert_success

    # Check if log messages were written to the expected file
    local log_filename=$(find "$BACKUP_LOG_FOLDER" -type f -name "$BACKUP_LOGGING_STATIC_FILES_ROTATION_LOG_FILENAME*" | head -n 1)
    mapfile -t lines < <(tail -n 1 "$log_filename")  # read file lines to array
    mapfile -t log_message_elements < <(parse_log_message "${lines[0]}" "$BACKUP_LOG_FILE_SEPARATOR")
    assert_equal "${log_message_elements[1]}" "INFO"
    assert_equal "${log_message_elements[2]}" "rotate_static_files_backups"
    assert_equal "${log_message_elements[3]}" "Finished static files backup rotation"
}
