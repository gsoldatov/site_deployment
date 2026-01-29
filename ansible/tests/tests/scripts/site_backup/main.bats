# ansisble/scripts/site_backup/main.bash module tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'

    load '../../../../scripts/site_backup/main'

    # Create a temporary directory for each test case
    ensure_test_case_subdir

    # Test variables
    TEST_ENV_FILE="tests/test_helpers/mocks/site_backup/test_env_file"  # relative to "<project_root>/ansible"
    NON_EXISTING_ENV_FILE="tests/test_helpers/mocks/site_backup/non_existing.env"

    # Set default mocks for supplementary functions
    is_metered_connection() { return 0; }
    ping() { return 0; }
    
    # Set default mocks for db & static files backup execution via Ansible
    load '../../../test_helpers/mocks/site_backup/db_backup.bash'
    load '../../../test_helpers/mocks/site_backup/static_files_backup.bash'
}


@test "backup_main: missing env file option" {
    run backup_main
    assert_failure 1
    assert_output --partial "Missing --env-file option, exiting."
}


@test "backup_main: non-existing env file option" {
    run backup_main --env-file "$NON_EXISTING_ENV_FILE"
    assert_failure 1
    assert_output --regexp "Env file.*does not exist"
}


@test "backup_main: env file is sourced" {
    local test_case_flag_file="$TEST_CASE_TEMP_DIR/source_flag_file"
    # Override source function
    source() {
        eval "$(cat "$1")"
        printf "%s" "$FILE_SOURCE_FLAG" >> "$test_case_flag_file"
    }

    # Check if provided env file was sourced
    run backup_main --env-file "$TEST_ENV_FILE"
    assert_success
    assert_equal "$(cat "$test_case_flag_file")" "1"
}


@test "backup_main: db backup is triggered" {
    # Check if mock db backup was performed
    run backup_main --env-file "$TEST_ENV_FILE" --backup-db
    assert_success
    [ -f  "$BACKUP_DB_RUN_FILE" ]
    [ ! -f  "$BACKUP_STATIC_FILES_RUN_FILE" ]
}


@test "backup_main: static files backup is triggered" {
    # Check if mock static files backup was performed
    run backup_main --env-file "$TEST_ENV_FILE" --backup-static-files
    assert_success
    [ ! -f  "$BACKUP_DB_RUN_FILE" ]
    [ -f  "$BACKUP_STATIC_FILES_RUN_FILE" ]
}
