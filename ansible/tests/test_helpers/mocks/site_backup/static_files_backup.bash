# Mocks for a successful static files backup execution (via Ansible)
export BACKUP_STATIC_FILES_RUN_FILE="$TEST_CASE_TEMP_DIR/static_files_backup_run_file"    # file, which is written into, when a mock ansible backup command is run
export RUN_STATIC_FILES_BACKUP_COMMAND="bash -c 'echo \"triggered successful backup\" >> \"$BACKUP_STATIC_FILES_RUN_FILE\"; exit 0'"
