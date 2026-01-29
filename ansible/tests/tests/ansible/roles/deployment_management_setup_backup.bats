# ansisble/tasks/deployment_management_setup_backup role script tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'

    # Create temporary directories for all test-cases
    ensure_test_case_subdir

    # Set default mocks for db & static files backup execution via Ansible
    load '../../../test_helpers/mocks/site_backup/db_backup.bash'
    load '../../../test_helpers/mocks/site_backup/static_files_backup.bash'

    # Test variables
    SCRIPT_PATH="$PROJECT_ROOT/ansible/roles/deployment_management_setup_backup/scripts/site_backup.bash"
    TEST_ENV_FILE="tests/test_helpers/mocks/site_backup/test_env_file"  # relative to "<project_root>/ansible"
}


@test "site_backup: run without file logging" {
    # Check if mock db & static files backups were performed
    run "$SCRIPT_PATH" --env-file "$TEST_ENV_FILE" --backup-db --backup-static-files
    assert_success
    [ -f  "$BACKUP_DB_RUN_FILE" ]
    [ -f  "$BACKUP_STATIC_FILES_RUN_FILE" ]
}


@test "site_backup: run with file logging" {
    # Set environment variables, which enable logging
    export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
    export BACKUP_SCRIPT_LOG_FILENAME="backup.log"
    export BACKUP_LOG_FILE_SEPARATOR=";"

    # Check if mock db & static files backups were performed
    run "$SCRIPT_PATH" --env-file "$TEST_ENV_FILE" --backup-db --backup-static-files
    assert_success
    [ -f  "$BACKUP_DB_RUN_FILE" ]
    [ -f  "$BACKUP_STATIC_FILES_RUN_FILE" ]

    # Check if script log file appeared
    local last_log_line="$(tail -n1 "$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME")"
    [[ "$last_log_line" == *"Finished script execution."* ]] 
}
