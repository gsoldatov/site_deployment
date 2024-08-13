import os
import shutil
import subprocess

from monitoring.log_fetching.jobs.fetch_logs import FetchLogs


class FetchLocalLogs(FetchLogs):
    """
    Basic job for fetching local logs.
    Job algorithm:
    - prepare temp folder;
    - set full fetch mode and fetch period;
    - copy matching files into a temp folder and unarchive, if needed;
    - filter and transform data from fetched files;
    - upsert data into the database (replace existing data for the fetch period).
    """
    def get_matching_files(self):
        """ Find, copy and unarchive matching files into the temp folder. """
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
        
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        stdout, _ = proc.communicate()

        if proc.returncode > 0:
            raise Exception("Failed to get matching files.")
        
        if not stdout:
            self.log(self.name, "INFO", "Found no matching files.")
            return
        
        matching_files = stdout.decode("utf-8").strip().split("\n")
        self.number_of_matching_files = len(matching_files)

        # Copy files into the temp folder and unarchive
        for file in matching_files:
            file_copy = shutil.copy(file, self.temp_folder)
            if file_copy.endswith(".gz"):
                os.system(f"gunzip {file_copy}") # Replace gzipped `file` with unarchived file in the same directory
        
        self.log(self.name, "DEBUG", f"Copied {len(matching_files)} files into temp folder.")


    def run(self):
        # Setup
        self.log(self.name, "INFO", f"Starting job {self.name}.")
        self.prepare_local_temp_folder()
        self.set_full_fetch()
        self.set_fetch_period()

        # Find and copy matching files into temp folder
        self.get_matching_files()

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
