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
    Checks if any of the active internet connections.
    Returns:
    - 0 if no active connections are metered, 1 if at least one active;
    - 1 if at least one active connection is metered;
    - 2 if there is no active connections.
"
is_metered_connection() {
    local active_connections=$(nmcli -t -f NAME connection show --active)

    if [ -z $active_connections ]; then return 2; fi
        
    for conn in "$active_connections"; do
        is_metered=$(nmcli -t -f connection.metered connection show $conn | grep ':yes' | wc -l)
        if (( $is_metered == 1 )); then return 1; fi
    done

    return 0
}


: "
    Checks if variables, which names are passed
    as positional arguments, are defined and not empty
"
assert_variables() {
    local names=("$@")

    for name in "${names[@]}"; do
        if [ -z "${!name}" ]; then
            log_message "ERROR" "assert_variables" "Variable '$name' is not defined or empty"
            exit 1
        fi
    done
}
