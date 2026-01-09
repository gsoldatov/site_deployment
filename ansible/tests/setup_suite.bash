CURR_FILE=$(realpath "${BASH_SOURCE[0]}")
ANSIBLE_DIR="$(dirname "$(dirname "$CURR_FILE")")"    # <project_root>/ansible

# Directory for temporary files, created during test runs
# NOTE: must be equal to:
# - $TEMP_DIR in test_helpers/fixtures.bash
TEMP_DIR="$ANSIBLE_DIR/tests/temp"


setup_suite() {
    # NOTE: helpers can only be loaded in setup() function
    # for each test case and can't be loaded here due to
    # setup_suite() running in a different subshell

    # Ensure temp dir exists
    if [ ! -d "$TEMP_DIR" ]; then
        mkdir "$TEMP_DIR"
    fi

    # Clean temp dir contents
    find "$TEMP_DIR" -mindepth 1 -delete
}


teardown_suite() {
    :
    # # Clean temp dir contents
    # find "$TEMP_DIR" -mindepth 1 -delete
}