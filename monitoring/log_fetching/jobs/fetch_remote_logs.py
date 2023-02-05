import os
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
    def run_remote_commands(self):
        """ 
        Wrapper method for commands and functions which need an active SSH connection to the server.

        Default implementation gets server timezone and fetches matching files to the local machine.
        """
        self.get_server_timezone()
        self.fetch_files()


    def get_server_timezone(self):
        """ Gets production server's timezone. """
        result = self.ssh_connection.run('date +"%z"')
        d = datetime.strptime(result.stdout.strip(), "%z")
        self.server_timezone = d.tzinfo
    

    def fetch_files(self):
        """ Fetch files with matching pattern and modification time into temp folder. """
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

        # Exit if no matching files found
        if len(result.stdout.strip()) == 0:
            self.log(self.name, "INFO", "Found no matching files.")
            return
        
        remote_files = result.stdout.strip().split("\n")
        self.number_of_matching_files = len(remote_files)
        remote_filenames = " ".join((os.path.basename(f) for f in remote_files))
        self.log(self.name, "DEBUG", f"Found {len(remote_files)} matching files.")

        try:
            # Archive and fetch matching files
            archive_filename = f"/home/{self.config['server_user']}/tmp_{str(uuid4())[:8]}.tar.gz"
            local_archive_filename = os.path.join(self.temp_folder, os.path.basename(archive_filename))

            # tar params:
            # -c = create tar archive;
            # -z = gzip archive;
            # -f = archive filename;
            # -C = current working directory (required to create flat archive without recreating parent folders for archived files);
            # remote_filenames = list of space-separated files to archive, relative to directory specified in `-C` option.
            self.ssh_connection.sudo(f"tar -C '{self.log_folder}' -czf {archive_filename} {remote_filenames}")
            self.ssh_connection.sudo(f"chown {self.config['server_user']} {archive_filename}")
            
            self.ssh_connection.get(archive_filename, local=local_archive_filename)
            self.log(self.name, "DEBUG", f"Fetched matching files to the local machine.")

            # Unarchive tarball with fetched files and remove it
            os.system(f"tar -xzf '{local_archive_filename}' -C {self.temp_folder}")
            os.remove(local_archive_filename)

            # Unarchive fetched gzip archives
            archived_fetched_files = [os.path.join(self.temp_folder, f) for f in os.listdir(self.temp_folder) if f.endswith(".gz")]
            for file in archived_fetched_files:
                os.system(f"gunzip {file}") # Replace gzipped `file` with unarchived file in the same directory
            self.log(self.name, "DEBUG", f"Unarchived {len(archived_fetched_files)} files.")
        finally:
            # Remove archived files
            self.ssh_connection.sudo(f"rm -f {archive_filename}")


    def run(self):
        # Setup
        self.log(self.name, "INFO", f"Starting job {self.name}.")
        self.prepare_folder()
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
