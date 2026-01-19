# ansisble/scripts/common/util.bash module tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'
    
    load '../../../../scripts/common/logging'
    load '../../../../scripts/common/util'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "get_last_matching_line"
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


@test "assert_variables" {
    # No variable names
    run assert_variables
    assert_success

    # Single missing variable
    run assert_variables "a"
    assert_equal $status 1
    assert_output --partial "Variable 'a' is not defined or empty"

    # Empty variable
    a="a"
    b=""
    run assert_variables "a" "b"
    assert_equal $status 1
    assert_output --partial "Variable 'b' is not defined or empty"

    # All variables are defined
    b="b"
    run assert_variables "a" "b"
    assert_success
}


@test "get_last_matching_line" {
    # Add a temp file
    filepath="$TEST_CASE_TEMP_DIR/file.txt"
    echo "aaa bbb ccc" >> "$filepath"
    echo "aaa ccc ddd" >> "$filepath"
    echo "aaa ddd eee" >> "$filepath"

    # Missing required arguments
    run get_last_matching_line
    assert_equal $status 1
    assert_output --partial "get_last_matching_line expects at least 2 arguments"

    run get_last_matching_line "file_path"
    assert_equal $status 1
    assert_output --partial "get_last_matching_line expects at least 2 arguments"

    # Non-existing file
    run get_last_matching_line "$TEST_CASE_TEMP_DIR/non-existing.txt" "aaa"
    assert_success
    assert [ -z "$output" ]

    # Non-matching pattern
    run get_last_matching_line "$filepath" "non-existing pattern"
    assert_success
    assert [ -z "$output" ]

    # Matching single pattern
    run get_last_matching_line "$filepath" "aaa"
    assert_success
    assert_output "aaa ddd eee"

    # Matching multiple patterns
    run get_last_matching_line "$filepath" "aaa" "ccc"
    assert_success
    assert_output "aaa ccc ddd"

    # Non-matching multiple patterns
    run get_last_matching_line "$filepath" "aaa" "non-existing pattern"
    assert_success
    assert [ -z "$output" ]

    run get_last_matching_line "$filepath" "non-existing pattern" "aaa"
    assert_success
    assert [ -z "$output" ]
}
