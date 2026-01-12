# ansisble/scripts/common/rotate.bash module tests
setup() {
    load '../../../test_helpers/bats-assert/load'
    load '../../../test_helpers/bats-support/load'
    load '../../../test_helpers/fixtures'
    
    load '../../../../scripts/common/rotate.bash'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "rotate: backup disabled"
        "rotate: file does not exist"
        "rotate: rotate a file"
        "rotate: copies deletion"
        "rotate: rotate existing copies"
        "rotate: rotation intervals"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi
}


@test "rotate: missing and invalid arguments" {
    # Missing required arguments
    run rotate -f "a" -c 0 -i 0
    assert_equal $status 1
    assert_output --partial "Missing required argument"

    run rotate -p "$TEST_CASE_TEMP_DIR" -c 0 -i 0
    assert_equal $status 1
    assert_output --partial "Missing required argument"

    run rotate -p "$TEST_CASE_TEMP_DIR" -f "a" -i 0
    assert_equal $status 1
    assert_output --partial "Missing required argument"

    run rotate -p "$TEST_CASE_TEMP_DIR" -f "a" -c 0
    assert_equal $status 1
    assert_output --partial "Missing required argument"

    # Unexpected argument
    run rotate -p "$TEST_CASE_TEMP_DIR" -f "a" -c 0 -i 0 --unexpected
    assert_equal $status 1
    assert_output --partial "Unexpected argument"

    # Non-existing parent directory
    run rotate -p "$TEST_CASE_TEMP_DIR" -f "a" -c 0 -i 0
    assert_equal $status 1
    assert_output --partial "does not exist"

    # Non-numeric max_count & rotation_interval
    run rotate -p "$TEMP_DIR" -f "a" -c "a" -i 0
    assert_equal $status 1
    assert_output --partial "must be an integer"

    run rotate -p "$TEMP_DIR" -f "a" -c 0 -i "a"
    assert_equal $status 1
    assert_output --partial "must be an integer"
}


@test "rotate: backup disabled" {
    touch "$TEST_CASE_TEMP_DIR/a"

    for c in "0" "1"; do
        run rotate -p "$TEST_CASE_TEMP_DIR" -f "a" -c $c -i 0
        assert_success
        assert_output --partial "Rotation is disabled"
        if [[ -e "$TEST_CASE_TEMP_DIR/a.1" ]]; then
            fail "Found an unexpected rotated file"
        fi
    done
}


@test "rotate: file does not exist" {
    # Try to rotate a non-existing file
    run rotate -p "$TEST_CASE_TEMP_DIR" -f "missing.txt" -c 3 -i 1
    assert_success
    assert_output --partial "file '$TEST_CASE_TEMP_DIR/missing.txt' does not exist"
    assert [ ! -e "$TEST_CASE_TEMP_DIR/missing.txt" ]
    assert [ ! -e "$TEST_CASE_TEMP_DIR/missing.txt.1" ]
}


@test "rotate: rotate a file" {
    # Add a file & check if it's rotated
    touch "$TEST_CASE_TEMP_DIR/test.txt"

    run rotate -p "$TEST_CASE_TEMP_DIR" -f "test.txt" -c 3 -i 0
    assert_success

    assert [ -f "$TEST_CASE_TEMP_DIR/test.txt" ]
    assert [ -f "$TEST_CASE_TEMP_DIR/test.txt.1" ]
    assert [ ! -e "$TEST_CASE_TEMP_DIR/test.txt.2" ]
}


@test "rotate: rotate a directory" {
    mkdir -p "$TEST_CASE_TEMP_DIR/data"
    touch "$TEST_CASE_TEMP_DIR/data/file.txt"

    run rotate -p "$TEST_CASE_TEMP_DIR" -f "data" -c 3 -i 0
    assert_success

    assert [ -d "$TEST_CASE_TEMP_DIR/data" ]
    assert [ -d "$TEST_CASE_TEMP_DIR/data.1" ]
    assert [ -f "$TEST_CASE_TEMP_DIR/data.1/file.txt" ]
}


@test "rotate: copies deletion" {
    echo "v0" > "$TEST_CASE_TEMP_DIR/app.log"
    echo "v1" > "$TEST_CASE_TEMP_DIR/app.log.1"
    echo "v2" > "$TEST_CASE_TEMP_DIR/app.log.2"
    touch "$TEST_CASE_TEMP_DIR/app.log.3"
    touch "$TEST_CASE_TEMP_DIR/app.log.bak"

    run rotate -p "$TEST_CASE_TEMP_DIR" -f "app.log" -c 3 -i 0
    assert_success

    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log")" = "v0" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log.1")" = "v0" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log.2")" = "v1" ]
    assert [ ! -e "$TEST_CASE_TEMP_DIR/app.log.3" ]
    assert [ ! -e "$TEST_CASE_TEMP_DIR/app.log.4" ]
    assert [ -f "$TEST_CASE_TEMP_DIR/app.log.bak" ]  # Files with non-numeric suffix are not deleted
}


@test "rotate: rotate existing copies" {
    echo "v0" > "$TEST_CASE_TEMP_DIR/app.log"
    echo "v1" > "$TEST_CASE_TEMP_DIR/app.log.1"
    echo "v2" > "$TEST_CASE_TEMP_DIR/app.log.2"

    run rotate -p "$TEST_CASE_TEMP_DIR" -f "app.log" -c 4 -i 0
    assert_success

    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log")" = "v0" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log.1")" = "v0" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log.2")" = "v1" ]
    assert [ "$(cat "$TEST_CASE_TEMP_DIR/app.log.3")" = "v2" ]
}


@test "rotate: rotation intervals" {
    touch "$TEST_CASE_TEMP_DIR/access.log"

    # Try to rotate before the rotation interval has passed
    run rotate -p "$TEST_CASE_TEMP_DIR" -f "access.log" -c 3 -i 60
    assert_success
    assert_output --partial "Skipping rotation until"
    assert [ ! -e "$TEST_CASE_TEMP_DIR/access.log.1" ]

    # Rotate after an interval has passed
    sleep 1
    run rotate -p "$TEST_CASE_TEMP_DIR" -f "access.log" -c 3 -i 1
    assert_success
    assert [ -f "$TEST_CASE_TEMP_DIR/access.log.1" ]
}
