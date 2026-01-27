# ansisble/scripts/site_backup/util.bash module tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'

    load '../../../../scripts/site_backup/util'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "get_last_log_message_time: finds earliest message in current log"
        "get_last_log_message_time: finds message in archived log"
        "get_last_log_message_time: returns default when no matches exist"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi

    # Export required global variables
    test_cases_without_preset_variables=(
       "get_last_log_message_time: required global variables"
    )

    if ! printf '%s\n' "${test_cases_without_preset_variables[@]}" | grep -Fxq -- "$BATS_TEST_DESCRIPTION"; then
        export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
        export BACKUP_SCRIPT_LOG_FILENAME="backup.log"
        export BACKUP_LOG_FILE_SEPARATOR=";"
    fi
}


@test "get_last_log_message_time: required global variables" {
    run get_last_log_message_time "pattern"
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_LOG_FOLDER' is not defined or empty"

    export BACKUP_LOG_FOLDER="$TEST_CASE_TEMP_DIR"
    run get_last_log_message_time "pattern"
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_SCRIPT_LOG_FILENAME' is not defined or empty"

    export BACKUP_SCRIPT_LOG_FILENAME="backup.log"
    run get_last_log_message_time "pattern"
    assert_failure 1
    assert_output --partial "Variable 'BACKUP_LOG_FILE_SEPARATOR' is not defined or empty"
}


@test "get_last_log_message_time: requires pattern argument" {
    run get_last_log_message_time
    assert_failure 1
    assert_output --partial "Missing required search pattern"
}


@test "get_last_log_message_time: finds earliest message in current log" {
    # Create a log file with messages
    local log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
    local first_datetime="2001-01-01T11:11:11 +00:00"
    local second_datetime="2002-02-02T22:22:22 +00:00"

    echo "$first_datetime;INFO;test;first" >> "$log_file"
    echo "$second_datetime;INFO;test;second" >> "$log_file"

    # Check if correct timestamp is returned
    run get_last_log_message_time "first"
    # # bats adds stderr to output by default, so function output is taken
    # # from the last line of output to separate it from log messages
    local timestamp=$(echo "$output" | tail -n1)
    assert_success
    assert_equal "$timestamp" $(date -d "$first_datetime" +%s)
}


@test "get_last_log_message_time: finds message in archived log" {
    # Create current log file
    local log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
    local second_datetime="2002-02-02T22:22:22 +00:00"
    echo "$second_datetime;INFO;test;second" >> "$log_file"

    # Create an archived log file
    local archived_log_file_temp="$BACKUP_LOG_FOLDER/tmp"
    echo "$first_datetime;INFO;test;first" >> "$archived_log_file_temp"
    local archive_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME.1.gz"
    gzip -c "$archived_log_file_temp" > "$archive_file"

    # Check if correct timestamp is returned
    run get_last_log_message_time "first"
    # # bats adds stderr to output by default, so function output is taken
    # # from the last line of output to separate it from log messages
    local timestamp=$(echo "$output" | tail -n1)
    assert_success
    assert_equal "$timestamp" $(date -d "$first_datetime" +%s)
}


@test "get_last_log_message_time: returns default when no matches exist" {
    # Create current log file
    local log_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME"
    local second_datetime="2002-02-02T22:22:22 +00:00"
    echo "$second_datetime;INFO;test;second" >> "$log_file"

    # Create an archived log file
    local archived_log_file_temp="$BACKUP_LOG_FOLDER/tmp"
    echo "$first_datetime;INFO;test;first" >> "$archived_log_file_temp"
    local archive_file="$BACKUP_LOG_FOLDER/$BACKUP_SCRIPT_LOG_FILENAME.1.gz"
    gzip -c "$archived_log_file_temp" > "$archive_file"

    # Check if correct timestamp is returned
    run get_last_log_message_time "non-existing"
    # # bats adds stderr to output by default, so function output is taken
    # # from the last line of output to separate it from log messages
    local timestamp=$(echo "$output" | tail -n1)
    assert_success
    assert_equal "$timestamp" 0
}
