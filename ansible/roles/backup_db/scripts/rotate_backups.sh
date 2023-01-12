# Rotates existing backup copies before the fetch of a new backup
FILEPATH_TEMPLATE="$BACKUP_LOCAL_FOLDER/$BACKUP_DB_DUMP_FILENAME"

# Do nothing if a single copy is kept
if (($BACKUP_DB_MAX_BACKUP_COUNT <= 1)); then
    echo "\$BACKUP_DB_MAX_BACKUP_COUNT <= 1, exiting."
    exit 0
fi

# Delete the backup with the maximum number
FILEPATH="$FILEPATH_TEMPLATE.$(($BACKUP_DB_MAX_BACKUP_COUNT - 1))"
if [[ -f "$FILEPATH" ]]; then
    echo "REMOVING $FILEPATH"
    rm -f "$FILEPATH"
fi

# Increase backup numbers
for ((i = $BACKUP_DB_MAX_BACKUP_COUNT - 1; i > 1; i--))
do
    FROM="$FILEPATH_TEMPLATE.$(($i - 1))"
    TO="$FILEPATH_TEMPLATE.$i"
    echo "i = $i"

    if [[ -f "$FROM" ]]; then
        echo "MOVING FROM $FROM TO $TO"
        mv $FROM $TO
    fi
done

# Set number on the most recent backup
if [[ -f "$FILEPATH_TEMPLATE" ]]; then
    echo "MOVING FROM $FILEPATH_TEMPLATE TO $FILEPATH_TEMPLATE.1"
    mv $FILEPATH_TEMPLATE "$FILEPATH_TEMPLATE.1"
fi
