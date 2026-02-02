# Mocks for a failing databse backup execution (via Ansible)
export BACKUP_DB_RUN_FILE="$TEST_CASE_TEMP_DIR/db_backup_run_file"    # file, which is written into, when a mock ansible backup command is run
export RUN_DB_BACKUP_COMMAND="bash -c 'echo \"triggered failing backup\" >> \"$BACKUP_DB_RUN_FILE\"'; exit 1"
