import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from monitoring.log_fetching.jobs.fetch_logs import FetchLogs


class FetchRemoteLogs(FetchLogs):
    """
    Basic job for fetching remote logs.
    Job algorithm:
    - prepare temp folder;
    - set full fetch mode and fetch period;
    - connect to remote server and run specified commands over SSH:
        - default implementation fetches matching files and server timezone;
    - filter and transform data from fetched files;
    - upsert data into the database (replace existing data for the fetch period).
    """
    def __init__(self, name, args, config, db_connection, log, log_folder, filename_patterns, separator):
        super().__init__(name, args, config, db_connection, log, log_folder, filename_patterns, separator)

        self.remote_temp_folder = Path(self.config["fetched_logs_settings"]["remote_temp_folder"]) / self.name

    def run_remote_commands(self):
        """ 
        Wrapper method for commands and functions which need an active SSH connection to the server.

        Default implementation gets server timezone and fetches matching files to the local machine.
        """
        self.prepare_remote_temp_folder()
        self.get_server_timezone()
        self.fetch_files()    


    def prepare_remote_temp_folder(self):
        """ Ensure remote temp folder is present & clean. """
        self.ssh_connection.run(f"mkdir -p '{self.remote_temp_folder}'")
        self.ssh_connection.sudo(f"find '{self.remote_temp_folder}' -mindepth 1 -delete")
        # rm_pattern = self.remote_temp_folder / "*"
        # self.ssh_connection.sudo(f"rm -rf '{rm_pattern}'")    # shell expansion does not work for quoted paths


    def get_server_timezone(self):
        """ Gets production server's timezone. """
        result = self.ssh_connection.run('date +"%z"')
        d = datetime.strptime(result.stdout.strip(), "%z")
        self.server_timezone = d.tzinfo
    

    def fetch_files(self, copy_log_files_to_temp_dir = True):
        """
        Fetch files with matching pattern and modification time into temp folder.
        
        If `copy_log_files_to_temp_dir` is set to true, log files are copied into temp folder
        before they're archived & fetched to local machine (otherwise, they're expected to be present in the temp folder).
        """
        # Get matching files
        cmd = f'find "{self.log_folder}" -mindepth 1'
        if type(self.filename_patterns) == str: cmd += f' -name "{self.filename_patterns}"'
        if type(self.filename_patterns) == list: # add -name option for each pattern in list, e.g.: '\( -name "p1" -o -name "p2" \)'
            cmd += ' \\(' + \
                ' -o'.join((f' -name "{p}"' for p in self.filename_patterns)) + \
                    ' \\)'
        
        if not self.full_fetch:  # Filter files by time if not running full fetch
            t = self.min_time.isoformat()
            cmd +=  f' -newermt "{t}"'
        result = self.ssh_connection.sudo(cmd)

        stdout = result.stdout
        newline_index = stdout.find("\n")   # remove sudo password prompt line
        stdout = stdout[newline_index + 1:].strip()

        # Exit if no matching files found
        if len(stdout) == 0:
            self.log(self.name, "INFO", "Found no matching files.")
            return

        remote_files = stdout.split("\n")
        remote_files = [f.strip() for f in remote_files]    # Additional stripping for the case of CR+LF line separation
        
        self.number_of_matching_files = len(remote_files)
        self.log(self.name, "DEBUG", f"Found {len(remote_files)} matching files.")

        # Copy files to temp folder
        if copy_log_files_to_temp_dir:
            quoted_remote_files = " ".join((f"'{f}'" for f in remote_files))
            self.ssh_connection.sudo(f"cp {quoted_remote_files} '{self.remote_temp_folder}'")
            self.log(self.name, "DEBUG", f"Copied matching files into temp folder.")
            
        # Archive and fetch matching files
        archive_file = self.remote_temp_folder / f"tmp_{str(uuid4())[:8]}.tar.gz"
        local_temp_folder = Path(self.local_temp_folder)
        local_archive_file = local_temp_folder / archive_file.name

        # tar params:
        # -c = create tar archive;
        # -z = gzip archive;
        # -f = archive filename;
        # -C = current working directory (required to create flat archive without recreating parent folders for archived files);
        # quoted_remote_filenames = list of space-separated files to archive, relative to directory specified in `-C` option.
        quoted_remote_filenames = " ".join((f"'{Path(f).name}'" for f in remote_files))
        self.ssh_connection.sudo(f"tar -C '{self.remote_temp_folder}' -czf '{archive_file}' {quoted_remote_filenames}")
        self.ssh_connection.sudo(f"chown '{self.config['server_user']}' '{archive_file}'")
        
        # Fetch files to the local machine
        self.ssh_connection.get(str(archive_file), local=str(local_archive_file))
        self.log(self.name, "DEBUG", f"Fetched matching files to the local machine.")

        # Unarchive tarball with fetched files and remove it
        os.system(f"tar -xzf '{local_archive_file}' -C {self.local_temp_folder}")
        os.remove(local_archive_file)

        # Unarchive fetched gzip archives
        archived_fetched_files = [f for f in local_temp_folder.glob("*.gz")]
        for file in archived_fetched_files:
            os.system(f"gunzip '{file}'") # Replace gzipped `file` with unarchived file in the same directory
        self.log(self.name, "DEBUG", f"Unarchived {len(archived_fetched_files)} files.")


    def run(self):
        # Setup
        self.log(self.name, "INFO", f"Starting job {self.name}.")
        self.prepare_local_temp_folder()
        self.set_full_fetch()
        self.set_fetch_period()

        # Find and fetch matching files from server and get its timezone
        self.connect_and_run_remote_commands()

        if self.number_of_matching_files == 0: return

        # Scan files
        self.scan_files()

        # Update database
        try:
            with self.db_connection.cursor() as cursor:
                self.remove_existing_data(cursor)
                self.process_files(cursor)
            
            if self.number_of_inserted_records > 0:
                self.db_connection.commit()
            else:
                self.db_connection.rollback()
        except:
            self.db_connection.rollback()
            raise
        
        self.log(self.name, "INFO", f"Read {self.number_of_read_records} records, inserted {self.number_of_inserted_records}.")
