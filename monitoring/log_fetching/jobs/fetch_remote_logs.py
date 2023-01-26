import os
from shutil import rmtree
from datetime import datetime, timedelta
from uuid import uuid4

from fabric import Connection, Config
from psycopg2.extensions import AsIs

from monitoring.db.util import connect
from monitoring.log_fetching.jobs.base_job import BaseJob
from monitoring.util.util import get_local_tz


class FetchRemoteLogs(BaseJob):
    """
    Basic job for fetching remote logs.
    Job algorithm:
    - prepare local folder for file fetching;
    - get `min_time` & `max_time` based on script args (if provided) or last execution time;
    - connects to prod server & fetches all files, which match the pattern and were modified after `min_time`;
    - unarchives fetched files if required;
    - deletes existing data for the specified period;
    - reads each fetched file:
        - filters lines by timestamp in the first field being between `min_time` and `max_time` (timestamp is considered to be in the timezone of the prod server);
        - transforms matching lines (specific line transformations are provided by subclasses);
        - inserts matching lines into the database.
    """
    def __init__(self, name, args, config, log, remote_log_folder, filename_pattern, separator):
        super().__init__(name, args, config, log)

        self.remote_log_folder = remote_log_folder
        self.filename_pattern = filename_pattern
        self.separator = separator

        self.min_time = None
        self.max_time = None
        self.server_timezone = None

        self._db_connection = None
        self.ssh_connection = None
        self.temp_folder = None

        self.number_of_read_records = 0
        self.number_of_inserted_records = 0
    
    
    @property
    def db_connection(self):
        if not self._db_connection:
            self._db_connection = connect(self.config, db="logs")
        return self._db_connection
    
    
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
    

    def set_fetch_period(self):
        """ Sets min and max time of data to be fetched. """
        # Max time (from args or end of next day)
        now = datetime.now()
        self.max_time = self.args.max_time or \
            now.replace(hour=23, minute=59, second=59, microsecond=0, tzinfo=get_local_tz()) + timedelta(days=1)
        
        # Min time (from args, or based on max record_time)
        if self.args.min_time:
            self.min_time = self.args.min_time
        else:
            with self.db_connection.cursor() as cursor:
                cursor.execute(f"SELECT MAX(record_time) FROM {self.name}")
                row = cursor.fetchone() or []
                if row[0]:
                    self.min_time = row[0].replace(microsecond=0) + timedelta(seconds=1)
                else:
                    self.min_time = now.replace(year=now.year - 1, month=1, day=1, hour=0, 
                                                minute=0, second=0, microsecond=0, tzinfo=get_local_tz())
            
            self.db_connection.commit() # Close transaction
        
        self.log(f"Fetching data from {self.min_time.isoformat()} to {self.max_time.isoformat()}")

    
    def start_ssh_connection(self):
        """ Starts SSH connection to the production server. """
        config = Config(overrides={
            # Don't write command output in stdout & setup password for automatic sudo entering
            "run": {"hide": True},
            "sudo": {"password": self.config["server_user_password"], "hide": True}
        })
        self.ssh_connection = Connection(
            host=self.config["server_addr"],
            port=self.config["ssh_port"], 
            user=self.config["server_user"],
            connect_kwargs={ "key_filename": self.config["ssh_key_path"] },
            config=config
        )


    def get_server_timezone(self):
        """ Gets production server's timezone. """
        result = self.ssh_connection.run('date +"%z"')
        d = datetime.strptime(result.stdout.strip(), "%z")
        self.server_timezone = d.tzinfo
    

    def fetch_files(self):
        """ Fetch files with matching pattern and modification time into temp folder. """
        # Get matching files
        t = self.min_time.isoformat()
        cmd = f'find "{self.remote_log_folder}" -name "{self.filename_pattern}" -newermt "{t}"' # NOTE: remove -newermt if time filter should not be used
        result = self.ssh_connection.sudo(cmd)

        # Exit if no matching files found
        if not len(result.stdout.strip()):
            self.log("Found no matching files.")
            exit(0)
        
        remote_files = result.stdout.strip().split("\n")
        remote_filenames = " ".join((os.path.basename(f) for f in remote_files))
        self.log(f"Found {len(remote_files)} matching files.")

        try:
            # Archive and fetch matching files
            archive_filename = f"/tmp_{str(uuid4())[:8]}.tar.gz"
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
            self.log(f"Fetched matching files to the local machine.")

            # Unarchive tarball with fetched files and remove it
            os.system(f"tar -xzf '{local_archive_filename}' -C {self.temp_folder}")
            os.remove(local_archive_filename)

            # Unarchive fetched gzip archives
            archived_fetched_files = [os.path.join(self.temp_folder, f) for f in os.listdir(self.temp_folder) if f.endswith(".gz")]
            for file in archived_fetched_files:
                os.system(f"gunzip {file}") # Replace gzipped `file` with unarchived file in the same directory
            self.log(f"Unarchived {len(archived_fetched_files)} files.")
        finally:
            # Remove archived files
            self.ssh_connection.sudo(f"rm -f {archive_filename}")


    def remove_existing_data(self, cursor):
        """ Delete existing data for the fetch period in the database. """
        cursor.execute("DELETE FROM %s WHERE record_time BETWEEN %s AND %s", 
            (AsIs(self.name), self.min_time, self.max_time))


    def process_files(self, cursor):
        """ Read fetched files, transform and insert matching lines into the database. """
        files = [os.path.join(self.temp_folder, f) for f in os.listdir(self.temp_folder) if not f.endswith(".tar.gz")]

        for file in files:
            new_records = []

            with open(file, "r") as f:
                for line in f.readlines():
                    self.number_of_read_records += 1
                    if self.filter_line(line):
                        self.number_of_inserted_records += 1
                        new_records.append(self.transform_line(line))
            
            self.insert_data(new_records, cursor)
    

    def parse_timestamp(self, timestamp):
        """
        Converts string timestamp into a datetime object with server timezone
        Append 3 trailing zeroes to parse fraction part as microseconds.
        """
        return datetime.strptime(timestamp + "000", "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=self.server_timezone)
    

    def filter_line(self, line):
        """ 
        Filters line based on the timestamp in the first column of the line.
        Returns true if timestamp is inside the fetch period.
        Raises ValueError if timestamp could not be parsed.
        Expects timestamp in a 'YYYY-MM-DD hh:mm:ss,fff' format, consideres it to be in the timezone of the server.
        """
        record_time = self.parse_timestamp(line.split(self.separator)[0])
        return self.min_time <= record_time <= self.max_time


    def transform_line(self, line):
        """ Interface method, which transforms a valid log line into a tuple, which can be inserted into the database. """
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
        try:
            # Setup
            self.log(f"Starting job {self.name}.")
            self.prepare_folder()
            self.set_fetch_period()

            # Get files
            try:
                self.start_ssh_connection()
                self.get_server_timezone()
                self.fetch_files()
            finally:
                # Close ssh connection
                self.ssh_connection.close()

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
            
            self.log(f"Read {self.number_of_read_records} records, inserted {self.number_of_inserted_records}.")                

        finally:
            # Close conneciton
            if self.db_connection:
                if not self.db_connection.closed:
                    self.db_connection.close()
    