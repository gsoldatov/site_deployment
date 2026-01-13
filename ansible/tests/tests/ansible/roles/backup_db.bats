# ansisble/tasks/backup_db task tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "rotate_db_backups: run backup rotation script"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi
}


@test "rotate_db_backups: run backup rotation script" {
    local script_path="$PROJECT_ROOT/ansible/roles/backup_db/scripts/rotate_db_backups.bash"
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
    