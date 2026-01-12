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
Rotates a file or a directory
and keeps the specified amount of previous versions.

Required arguments:
    -p, --parent-directory
        path to the file's parent directory
    -f, --filename
        base name of the file to be rotated
    -c, --max-count
        maximum amount of file versions to be kept (setting to <=1 disables rotation)
    -i, --rotation-interval
        minimum interval in seconds between rotations
"
rotate() {
    # Parse args
    while (( "$#" )); do
        case "$1" in
            -p | --parent-directory) local parent_directory="$2"; shift; shift;;
            -f | --filename) local filename="$2"; shift; shift;;
            -c | --max-count) local max_count="$2"; shift; shift;;
            -i | --rotation-interval) local rotation_interval="$2"; shift; shift;;
            *)
                log_message "ERROR" "rotate" "Unexpected argument '$1'"
                exit 1
        esac
    done

    # Validate args
    for arg in "parent_directory" "filename" "max_count" "rotation_interval"; do
        if [ -z "${!arg}" ]; then
            log_message "ERROR" "rotate" "Missing required argument '$arg'"
            exit 1
        fi
    done

    if [ ! -d "$parent_directory" ]; then
        log_message "ERROR" "rotate" "Parent directory '$parent_directory' does not exist"
        exit 1
    fi

    for arg in "max_count" "rotation_interval"; do
        if ! [[ "${!arg}" =~ ^[+-]?[0-9]+$ ]]; then
            log_message "ERROR" "rotate" "$arg must be an integer"
            exit 1
        fi
    done

    log_message "INFO" "rotate" "Running with args: parent_directory = '$parent_directory', filename = '$filename', max_count = $max_count, rotation_interval = $rotation_interval"

    # Exit, if rotation is disabled
    if (( $max_count <= 1 )); then
        log_message "INFO" "rotate" "Rotation is disabled"
        exit 0
    fi

    # Do not rotate, if current file does not exist
    local current_file="$parent_directory/$filename"
    if ! [[ -e "$current_file" ]]; then
        log_message "INFO" "rotate" "Skipping rotation, because file '$current_file' does not exist"
        exit 0
    fi

    # Do not rotate, if current file was rotated recently
    local current_time=$(date +%s)
    local file_creation_time=$(stat -c %W "$current_file")
    local rotation_time=$((file_creation_time + rotation_interval))
    
    if (( current_time < rotation_time )); then
        log_message "INFO" "rotate" "Skipping rotation until $(date -d "@$rotation_time")"
        exit 0
    fi

    # Delete copies beyond max count
    find "$parent_directory" -maxdepth 1 -name "$filename.*" -print0 | while IFS= read -r -d $'\0' file_copy; do
        local suffix="${file_copy##*.}"
        
        if ! [[ "$suffix" =~ ^[0-9]+$ ]]; then
            log_message "WARNING" "rotate" "Invalid file copy suffix in '$file_copy'"
            continue
        fi

        if (( suffix >= max_count - 1 )); then
            log_message "INFO" "rotate" "Deleting old file copy: '$file_copy'"
            rm -rf "$file_copy"
        fi
    done

    # Rotate existing copies
    for (( i=max_count-1; i>=1; i-- )); do
        local old_version="$current_file.$i"
        local new_version="$current_file.$((i+1))"
        
        if [ -e "$old_version" ]; then
            log_message "INFO" "rotate" "Renaming '$old_version' to '$new_version'"
            mv "$old_version" "$new_version"
        fi
    done

    # Copy current file
    log_message "INFO" "rotate" "Renaming current file to ${current_file}.1"
    cp -r "$current_file" "${current_file}.1"
}
