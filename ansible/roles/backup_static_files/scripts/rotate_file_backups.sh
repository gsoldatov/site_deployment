# Rotates files specified in `ROTATED_FILES` environment variable


: "
    Rotates existing versions of a file, which absolute path was provided as an argument
"
rotate_file () {
    local FILE=$1

    # Do nothing if file does not exist
    if [[ ! -f $FILE ]]; then
        printf "File '$FILE' does not exist.\n"
        return 0
    fi

    # Delete maximum allowed version of the file
    local CURR_PATH="$FILE.$(($BACKUP_STATIC_FILES_MAX_BACKUP_COUNT - 1))"
    if [[ -f "$CURR_PATH" ]]; then
        printf "Removing $CURR_PATH\n"
        rm -f "$CURR_PATH"
    fi

    # Increase backup numbers
    for ((i = $BACKUP_STATIC_FILES_MAX_BACKUP_COUNT - 1; i > 1; i--))
    do
        FROM="$FILE.$(($i - 1))"
        TO="$FILE.$i"

        if [[ -f "$FROM" ]]; then
            printf "Moving $FROM to $TO\n"
            mv "$FROM" "$TO"
        fi
    done

    # Set number on the most recent backup
    if [[ -f "$FILE" ]]; then
        printf "Moving $FILE to $FILE.1\n"
        mv "$FILE" "$FILE.1"
    fi
}


: '
    Parses file paths from $ROTATED_FILES variable into 'ROTATED_FILE_PATHS' array.
    $ROTATED_FILES is expected to be a string with space-separated paths wrapped in double quotes.
'
parse_rotated_files () {
    local IN_PATH=0
    local ESCAPED_CHAR=0
    local CURRENT_PATH=''

    for (( i=0; i<${#ROTATED_FILES}; i++ )); do
        local CHAR=${ROTATED_FILES:$i:1}
        # printf "\n\n"
        # printf 'CHAR="%s" CURRENT_PATH="%s" IN_PATH=%s ESCAPED_CHAR=%s\n' "$CHAR" "$CURRENT_PATH" "$IN_PATH" "$ESCAPED_CHAR"
        # printf "ROTATED_FILE_PATHS=${ROTATED_FILE_PATHS[*]}\n"
        
        # Currently outside of a path
        if (($IN_PATH == 0)); then
            if [[ "$CHAR" == '"' ]]; then
                IN_PATH=1
                # printf "Set IN_PATH=1"
            elif [[ "$CHAR" != ' ' ]]; then
                printf "Incorrect \$ROTATED_FILES format at pos $i: expected a space or a double quote char."
                exit 1
            # else
            #     printf "Skipped space char"
            fi
        
        # Currently processing a path
        else
            # Current char is not escaped
            if (($ESCAPED_CHAR == 0)); then
                # Found an escaped char
                if [[ $CHAR == '\' ]]; then
                    ESCAPED_CHAR=1
                    # printf "Set ESCAPED_CHAR=1"
                
                # Found a regular character
                elif [[ $CHAR != '"' ]]; then
                    CURRENT_PATH="$CURRENT_PATH$CHAR"
                    # printf "Added char to current path"

                # Found end of current path
                else
                    if [[ ROTATED_FILE_PATHS != '' ]]; then
                        ROTATED_FILE_PATHS="$ROTATED_FILE_PATHS\n"
                    fi
                    ROTATED_FILE_PATHS="$ROTATED_FILE_PATHS$CURRENT_PATH"
                    CURRENT_PATH=''
                    IN_PATH=0
                    # printf "Added current path to ROTATED_FILE_PATHS"
                fi

            # Current char is escaped
            else
                # Current char can be escaped
                if [[ $CHAR == '\' || $CHAR == '"' ]]; then
                    CURRENT_PATH="$CURRENT_PATH$CHAR"
                    ESCAPED_CHAR=0
                    # printf "Added escaped char to current path"
                
                # Invalid escaped char
                else
                    printf "Incorrect \$ROTATED_FILES format at pos $i: only '\\' or '\"' chars can be escaped."
                    exit 1
                fi
            fi
        fi
    done

    if (($IN_PATH == 1)); then
        printf "Incorrect \$ROTATED_FILES format: last paths was not closed with a double quote char."
        exit 1
    fi
    
    printf "$ROTATED_FILE_PATHS"
    return 0
}


: '
    Iterate over newline-separated paths in $ROTATED_FILE_PATHS and rotate backups for each path.
'
rotate_file_paths() {
    local CURR_IFS="$IFS"
    IFS=$'\n'
    for ROTATED_FILE in "${ROTATED_FILE_PATHS[@]}"; do
        rotate_file $ROTATED_FILE
    done
    IFS=$CURR_IFS
}


# Parse environment variable with paths
ROTATED_FILE_PATHS=$(parse_rotated_files)
if (($? > 0)); then
    printf "$ROTATED_FILE_PATHS\n"
    exit 1
fi

# Rotate parsed paths
rotate_file_paths
