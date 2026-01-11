: "
    Joins strings (2nd and rest args) separated by a delimiter (1st arg).
    https://stackoverflow.com/a/17841619
"
join_by() {
  local d=${1-} f=${2-}
  if shift 2; then
    printf %s "$f" "${@/#/$d}"
  fi
}

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
