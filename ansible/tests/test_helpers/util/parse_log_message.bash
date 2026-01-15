: '
Accepts a log message line and a separator as positonal arguments.
Parses logged message line items into $log_message_elements array.
'
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
