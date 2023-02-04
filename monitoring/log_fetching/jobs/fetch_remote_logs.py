import os
from shutil import rmtree
from datetime import datetime, timedelta
from uuid import uuid4

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.base_job import BaseJob
from monitoring.util.util import get_current_time


class FetchRemoteLogs(BaseJob):
    """
    Basic job for fetching remote logs.
    Job algorithm:
    - prepare local folder for file fetching;
    - enable or disable full fetch mode based on script arg or
    - if not running full fetch mode, get `min_time` & `max_time` based on script args (if provided) or last full fetch mode execution time;
    - connects to prod server & fetches all files, which match the pattern and were modified after `min_time`;
    - unarchives fetched files if required;
    - if running full fetch mode, scan files and set fetch period based on data inside them;
    - deletes existing data for the specified period;
    - reads each fetched file:
        - filters lines by timestamp in the first field being between `min_time` and `max_time` (timestamp is considered to be in the timezone of the prod server);
        - transforms matching lines (specific line transformations are provided by subclasses);
        - inserts matching lines into the database.
    """
    def __init__(self, name, args, config, db_connection, log, remote_log_folder, filename_patterns, separator):
        super().__init__(name, args, config, db_connection, log)

        self.remote_log_folder = remote_log_folder
        self.filename_patterns = filename_patterns
        self.separator = separator
        self.timestamp_field_number = 0

        self.full_fetch = True
        self.min_time = None
        self.max_time = None
        self.server_timezone = None

        self.temp_folder = None

        self.number_of_matching_files = 0
        self.number_of_read_records = 0
        self.number_of_inserted_records = 0
    
    
    def prepare_folder(self):
        """ Ensures temp folder for fetched files is ready. """
        temp_folder = self.config["temp_folder"]
        if not os.path.isabs(temp_folder): 
            temp_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../", temp_folder))
        
        # Ensure temp folder & subfolder exist
        subfolder = os.path.join(temp_folder, self.name)
        self.temp_folder = subfolder
        os.makedirs(subfolder, exist_ok=True)

        # Clean existing subfolder contents
        for name in os.listdir(subfolder):
            filepath = os.path.join(subfolder, name)
            if os.path.isfile(filepath): os.remove(filepath)
            elif os.path.isdir(filepath): rmtree(filepath)
    

    def set_full_fetch(self):
        """ 
        Sets full fetch mode of the job to:
        1) True if --full-fetch script flag is passed;
        2) True if full fetch was never performed or performed more than a day ago;
        3) False, otherwise.
        """
        if not self.args.full_fetch:
            with self.db_connection: # Use connection as a context managaer to automatically commit/rollback transaction upon exit
                with self.db_connection.cursor() as cursor:
                    cursor.execute("SELECT last_successful_full_fetch_time FROM fetch_jobs_status WHERE job_name = %s", [self.name])
                    row = cursor.fetchone()
                    if row:
                        if row[0]:
                            if get_current_time() - row[0] < timedelta(days=1):
                                self.full_fetch = False
        self.log(self.name, "DEBUG", f"Full fetch mode is {'enabled' if self.full_fetch else 'disabled'}.")
    

    def set_fetch_period(self):
        """ Sets min and max time of data to be fetched. """
        # Set with temp values if running in full fetch mode (values will be later set based on fetched file values)
        if self.full_fetch:
            self.min_time = get_current_time()
            self.max_time = get_current_time() - timedelta(days=365 * 10)
            return

        # Max time (from args or end of next day)
        now = get_current_time()
        self.max_time = self.args.max_time or \
            now.replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=1)
        
        # Min time (from args, or based on max record_time)
        if self.args.min_time:
            self.min_time = self.args.min_time
        else:
            with self.db_connection: # Use connection as a context managaer to automatically commit/rollback transaction upon exit
                with self.db_connection.cursor() as cursor:
                    cursor.execute("SELECT MAX(record_time) FROM %s", [AsIs(self.name)])
                    row = cursor.fetchone() or []
                    if row[0]:
                        self.min_time = row[0].replace(microsecond=0) + timedelta(seconds=1)
                    else:
                        self.min_time = now.replace(year=now.year - 1, month=1, day=1, hour=0, 
                                                    minute=0, second=0, microsecond=0)
        
        self.log(self.name, "DEBUG", f"Fetching data from {self.min_time.isoformat()} to {self.max_time.isoformat()}.")
    

    def run_remote_commands(self):
        """ 
        Wrapper method for running commands on server via SSH.
        By default, gets server timezone and fetches matching files to the local machine.
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
        cmd = f'find "{self.remote_log_folder}" -mindepth 1'
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
        self.number_of_matching_files = len(result.stdout.strip())
        if self.number_of_matching_files == 0:
            self.log(self.name, "INFO", "Found no matching files.")
            return
        
        remote_files = result.stdout.strip().split("\n")
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
            self.ssh_connection.sudo(f"tar -C '{self.remote_log_folder}' -czf {archive_filename} {remote_filenames}")
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


    def remove_existing_data(self, cursor):
        """ Delete existing data for the fetch period in the database. """
        cursor.execute("DELETE FROM %s WHERE record_time BETWEEN %s AND %s", 
            (AsIs(self.name), self.min_time, self.max_time))
    

    def scan_files(self):
        """ Sets `min_time` and `max_time` based on data in fetched files, when running in full fetch mode. """
        if self.full_fetch:
            files = [os.path.join(self.temp_folder, f) for f in os.listdir(self.temp_folder) if not f.endswith(".gz")]

            for file in files:
                with open(file, "r") as f:
                    for line in f.readlines():
                        fields = self.get_line_fields(line)
                        record_time = self.parse_timestamp(fields[self.timestamp_field_number])
                        self.min_time = min(self.min_time, record_time)
                        self.max_time = max(self.max_time, record_time)
            
            self.log(self.name, "DEBUG", f"Set fetch period based on data in files from {self.min_time.isoformat()} to {self.max_time.isoformat()}.")


    def process_files(self, cursor):
        """ Read fetched files, transform and insert matching lines into the database. """
        files = [os.path.join(self.temp_folder, f) for f in os.listdir(self.temp_folder) if not f.endswith(".gz")]

        for file in files:
            new_records = []

            with open(file, "r") as f:
                for line in f.readlines():
                    self.number_of_read_records += 1
                    fields = self.get_line_fields(line)
                    if self.filter_record(fields):
                        self.number_of_inserted_records += 1
                        new_records.append(self.transform_record(fields=fields, file=file))
            
            self.insert_data(new_records, cursor)
    

    def get_line_fields(self, line):
        """ Splits a string `line` into a list of separate fields. """
        return line.split(self.separator)
    

    def parse_timestamp(self, timestamp):
        """
        Converts string timestamp into a datetime object with server timezone
        Append 3 trailing zeroes to parse fraction part as microseconds.
        """
        return datetime.strptime(timestamp + "000", "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=self.server_timezone)
    

    def filter_record(self, fields):
        """ 
        Filters a record based on the timestamp in its `self.timestamp_field_number` field.
        Returns true if timestamp is inside the fetch period.
        Raises ValueError if timestamp could not be parsed.
        Expects timestamp in a 'YYYY-MM-DD hh:mm:ss,fff' format, consideres it to be in the timezone of the server.
        """
        record_time = self.parse_timestamp(fields[self.timestamp_field_number])
        return self.min_time <= record_time <= self.max_time


    def transform_record(self, **kwrags):
        """ Interface for a method, which transforms fields of a valid log record into a tuple, which can be inserted into the database. """
        raise NotImplementedError
    

    def insert_data(self, data, cursor):
        """ Run insert query for a list of tuples `data`. """
        if len(data) > 0:
            query = "INSERT INTO %s VALUES " + ", ".join(
                "(" + ", ".join("%s" for _ in range(len(data[0]))) + ")"
                for __ in range(len(data))
            )

            params = [AsIs(self.name)]
            for record in data:
                params.extend(record)
            
            cursor.execute(query, params)


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
