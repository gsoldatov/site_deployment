# Fixtures for test cases to be called in test-case setup/teardown functions, as needed

# Project root directory
# (resolved by finding the top-level directory of a git repository
# containing $BATS_TEST_DIRNAME directory)
export PROJECT_ROOT="$(git -C "$BATS_TEST_DIRNAME" rev-parse --show-toplevel)"

# NOTE: see tests/setup_suite.bash for other locations,
# where this directory is referenced
export TEMP_DIR="$PROJECT_ROOT/ansible/tests/temp"

# Sub-directory for a specific test-case
export TEST_CASE_TEMP_DIR="$TEMP_DIR/$BATS_TEST_DESCRIPTION"


ensure_test_case_subdir() {
    # Ensure a temporary sub-directory 
    # for the test-case exists
    if [ ! -d "$TEST_CASE_TEMP_DIR" ]; then
        mkdir "$TEST_CASE_TEMP_DIR"
    fi

    # Clean temp sub-directory contents
    find "$TEST_CASE_TEMP_DIR" -mindepth 1 -delete
}
