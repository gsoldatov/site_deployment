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
    
    Required args:
    -m | --message: log message text
    -s | --source: log message source

    Optional args:
    -l | --level: log message level (defaults to INFO)
    -f | --file: log file to write to (writes to stdout, if omitted, or an empty string is passed)
    --sep: line separator to use (defaults to '; ')
"
log_message() {
    # Parse args
    local file=""
    local sep="; "
    local level="INFO"
    local message=""
    local source=""


    while (( "$#" )); do    # Loop through input options, filter script options & save rest for Ansible
        case "$1" in
            -f | --file) file=$2; shift; shift;;
            --sep) sep=$2; shift; shift;;
            -l | --level) level=$2; shift; shift;;
            -m | --message) message=$2; shift; shift;;
            -s | --source) source=$2; shift; shift;;
            *) echo "log_message received an unexpected argument $1"; exit 1;;
        esac
    done

    # Validate required args
    for arg in "message" "source"; do
        if [ -z "${!arg}" ]; then
            echo "log_message is missing a required argument '$arg'"
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
