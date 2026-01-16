# Config-related tests
setup() {
    load '../test_helpers/bats-assert/load'
    load '../test_helpers/bats-support/load'
    load '../test_helpers/fixtures'

    # Create temporary directories for specific test-cases
    # https://stackoverflow.com/a/47541882
    file_using_test_cases=(
        "compare production.env and production.env.example"
    )
    if printf '%s\0' "${file_using_test_cases[@]}" | grep -Fxqz -- "$BATS_TEST_DESCRIPTION"; then
        ensure_test_case_subdir
    fi
}

@test "compare production.env and production.env.example" {
    local first="$PROJECT_ROOT/ansible/production.env"
    local second="$PROJECT_ROOT/ansible/production.env.example"
    local diff_file="${TEST_CASE_TEMP_DIR}/env_diff.txt"
    
    # Create temporary files for cleaned variable lists
    local first_clean="${TEST_CASE_TEMP_DIR}/first_vars.txt"
    local second_clean="${TEST_CASE_TEMP_DIR}/second_vars.txt"
    
    # Extract and sort exported variable names (ignore values/comments)
    grep -Eh '^\s*export\s+' "$first" | 
        sed -E 's/^\s*export\s+//; s/(=.*)|(#.*)//; s/\s+//g' |
        sort -u > "$first_clean"
        
    grep -Eh '^\s*export\s+' "$second" | 
        sed -E 's/^\s*export\s+//; s/(=.*)|(#.*)//; s/\s+//g' |
        sort -u > "$second_clean"
    
    # Compare variable sets and capture differences
    if ! comm -3 "$first_clean" "$second_clean" > "$diff_file"; then
        echo "Failed to compare environment files" >&2
        return 1
    fi
    
    # Fail test if differences found
    if [ -s "$diff_file" ]; then
        echo "ERROR: Environment files have different exported variables:" >&2
        cat "$diff_file" >&2
        return 1
    fi
}
