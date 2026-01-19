if [ ! -z "$BATS_TEST_DIRNAME" ]; then
    # If running tests
    PROJECT_ROOT="$(git -C "$BATS_TEST_DIRNAME" rev-parse --show-toplevel)"
else
    # If running a script on its own
    DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    PROJECT_ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
fi

source "$PROJECT_ROOT/ansible/scripts/common/util.bash"


: "
    Writes a log message to stdout or a file.

    Accepts log level, message source and message as positional arguments.

    Uses tho following global variables:
    - LOG_MESSAGE_FILE - the file to write to (if empty, message is written to stdout);
    - LOG_MESSAGE_SEP - separator character(-s) between message parts (is empty, defaults to '; ')
"
log_message() {
    # Set variables' values
    local level="$1"
    local source="$2"
    local message="$3"

    local file=""
    if [ ! -z "$LOG_MESSAGE_FILE" ]; then
        file="$LOG_MESSAGE_FILE"
    fi

    local sep="; "
    if [ ! -z "$LOG_MESSAGE_SEP" ]; then
        sep="$LOG_MESSAGE_SEP"
    fi

    # Validate required args
    for arg in "level" "source" "message"; do
        if [ -z "${!arg}" ]; then
            echo "log_message expects 3 non-empty positional arguments: level, source & message"
            exit 1
        fi
    done

    # Build a log line
    local timestamp=$(date "+%Y-%m-%dT%H:%M:%S %z")
    local line=$(join_by "$sep" "$timestamp" "$level" "$source" "$message")

    # Write the log line
    if [ -z "$file" ]; then
        echo "$line"
    else
        echo "$line" >> "$file"
    fi
}


: '
    Accepts a log message line and a separator as positonal arguments.
    Outputs each line element on a new line, which can then be assigned to an arry like this:
        mapfile -t my_array < <(parse_log_message "$line" "$sep")
'
parse_log_message() {
    local line="${1}"
    local sep="${2}"
    local us=$'\x1F'  # Unit separator character

    # Validate required args
    for arg in "line" "sep"; do
        if [ -z "${!arg}" ]; then
            echo "parse_log_message expects 2 non-empty positional arguments: line & sep"
            exit 1
        fi
    done
    
    # Handle multi-character separators by normalizing to US
    local adjusted_line="${line//"$sep"/"$us"}"
    local -a elements
    IFS="$us" read -r -a elements <<< "$adjusted_line"

    if [ "${#elements[@]}" -ne 4 ]; then
        echo "Invalid number of fields in log line (expected 4, got ${#elements[@]})" >&2
        exit 1
    fi

    # Output elements on separate lines
    printf '%s\n' "${elements[@]}"
}
