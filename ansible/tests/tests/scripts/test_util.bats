# ansisble/scripts/util.bash module tests
setup() {
    load '../../test_helpers/bats-assert/load'
    load '../../test_helpers/bats-support/load'
    load '../../test_helpers/fixtures'
    
    load '../../../scripts/util.bash'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "log_message write to file"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi

}


@test "join_by" {
    # No delimiter and joined strings
    run join_by
    assert_success
    assert_output ""

    # No delimiter and joined strings 
    run join_by ";"
    assert_success
    assert_output ""

    # Single joined string
    run join_by ";" "aaa"
    assert_success
    assert_output "aaa"

    # Multiple joined strings
    run join_by ";" "aaa" "bbb" "ccc"
    assert_success
    assert_output "aaa;bbb;ccc"

    # Multichar delimiter
    run join_by "~ " "aaa" "bbb" "ccc"
    assert_success
    assert_output "aaa~ bbb~ ccc"
}


@test "log_message positional arguments" {
    # Missing level
    run log_message
    assert_equal $status 1
    assert_output "log_message expects 3 non-empty positional arguments: level, source & message"

    # Missing source
    run log_message "INFO"
    assert_equal $status 1
    assert_output "log_message expects 3 non-empty positional arguments: level, source & message"

    # Missing message
    run log_message "INFO" "src"
    assert_equal $status 1
    assert_output "log_message expects 3 non-empty positional arguments: level, source & message"

    # Empty level
    run log_message "" "src" "msg"
    assert_equal $status 1
    assert_output "log_message expects 3 non-empty positional arguments: level, source & message"

    # Empty source
    run log_message "INFO" "" "msg"
    assert_equal $status 1
    assert_output "log_message expects 3 non-empty positional arguments: level, source & message"

    # Empty message
    run log_message "INFO" "src" ""
    assert_equal $status 1
    assert_output "log_message expects 3 non-empty positional arguments: level, source & message"
}


@test "log_message write to stdout + default/custom separator" {
    # Write to stdout with default separator
    run log_message "INFO" "src" "msg"
    assert_success
    parse_log_message "$output" "; "
    assert_equal "${log_message_elements[1]}" "INFO"
    assert_equal "${log_message_elements[2]}" "src"
    assert_equal "${log_message_elements[3]}" "msg"

    # Check message timestamp
    local now=$(date +%s)
    local log_timestamp="${log_message_elements[0]}"
    local log_timestamp_in_seconds=$(date -d "$log_timestamp" +%s)
    local diff=$((log_timestamp_in_seconds - now))
    if [[ $diff -lt 0 ]]; then
        diff=$((-diff))
    fi

    if [[ $diff -ge 1 ]]; then
        fail "Log timestamp '$log_timestamp' is too far off from current time '$(date)'"
    fi

    # Write to stdout with a custom separator
    LOG_MESSAGE_SEP="|"
    run log_message "WARNING" "src2" "msg2"
    assert_success
    parse_log_message "$output" "|"
    assert_equal "${log_message_elements[1]}" "WARNING"
    assert_equal "${log_message_elements[2]}" "src2"
    assert_equal "${log_message_elements[3]}" "msg2"
}


@test "log_message write to file" {
    # Set log file & separator
    LOG_MESSAGE_FILE="$TEST_CASE_TEMP_DIR/logfile"
    LOG_MESSAGE_SEP=";"

    # Write a line to the file
    run log_message "WARNING" "first src" "first msg"
    assert_success

    # Check if the file contains a line
    mapfile -t lines < <(tail -n 3 "$LOG_MESSAGE_FILE")  # read file lines to array
    if [ "${#lines[@]}" -ne 1 ]; then
        fail "Log file contains ${#lines[@]} lines instead of 1"
    fi

    # Check if line contains proper values
    parse_log_message "${lines[0]}" "$LOG_MESSAGE_SEP"
    assert_equal "${log_message_elements[1]}" "WARNING"
    assert_equal "${log_message_elements[2]}" "first src"
    assert_equal "${log_message_elements[3]}" "first msg"

    # Write a second line to the file
    run log_message "ERROR" "second src" "second msg"
    assert_success

    # Check if file contains 2 lines
    mapfile -t lines < <(tail -n 3 "$LOG_MESSAGE_FILE")  # read file lines to array
    if [ "${#lines[@]}" -ne 2 ]; then
        fail "Log file contains ${#lines[@]} lines instead of 2"
    fi

    # Check if lines contain proper values
    parse_log_message "${lines[0]}" "$LOG_MESSAGE_SEP"
    assert_equal "${log_message_elements[3]}" "first msg"

    parse_log_message "${lines[1]}" "$LOG_MESSAGE_SEP"
    assert_equal "${log_message_elements[3]}" "second msg"
}


# Parses logged messages into $log_message_elements array
parse_log_message() {
    local line="${1}"
    local sep="${2}"
    local us=$'\x1F'  # Unit separator character

    # Handle multi-character separators by normalizing to US
    local adjusted_line="${line//"$sep"/"$us"}"
    IFS="$us" read -r -a log_message_elements <<< "$adjusted_line"

    if [ "${#log_message_elements[@]}" -ne 4 ]; then
        echo "Invalid number of fields in log line (expected 4, got ${#log_message_elements[@]})"
        return 1
    fi

    declare -p log_message_elements 2>/dev/null || echo "declare -a log_message_elements=(${log_message_elements[*]})" >&2
    return 0
}
