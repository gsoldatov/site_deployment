import os
from shutil import rmtree
from datetime import datetime, timedelta

from psycopg2.extensions import AsIs

from monitoring.log_fetching.jobs.base_job import BaseJob
from monitoring.util.util import get_current_time


class FetchLogs(BaseJob):
    """
    Class with common functionality for local and remote log data fetching:
    - local temp folder preparation;
    - set full fetch mode on or off, based on passed cli arg or last successful full fetch time;
    - set fetch period:
        - based on timestamps insied fetched files, if running full fetch mode;
        - based on cli arg or max existing timestamp in the database;
    - fetched/copied file scanning for fetch period;
    - file processing, log line filtering;
    - data upserting into the database.
    """
    def __init__(self, name, args, config, db_connection, log, log_folder, filename_patterns, separator):
        super().__init__(name, args, config, db_connection, log)

        self.log_folder = log_folder
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
        """ Set up & clean temp folder for fetched files. """
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
        """ Set min and max time of data to be fetched. """
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


    def remove_existing_data(self, cursor):
        """ Delete existing data for the fetch period in the database. """
        cursor.execute("DELETE FROM %s WHERE record_time BETWEEN %s AND %s", 
            (AsIs(self.name), self.min_time, self.max_time))
    

    def scan_files(self):
        """ Set `min_time` and `max_time` based on data in fetched files, when running in full fetch mode. """
        if self.full_fetch:
            files = [os.path.join(self.temp_folder, f) for f in os.listdir(self.temp_folder) if not f.endswith(".gz")]

            for file in files:
                with open(file, "r", errors="replace") as f:
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

            with open(file, "r", errors="replace") as f:
                for line in f.readlines():
                    self.number_of_read_records += 1
                    fields = self.get_line_fields(line)
                    if self.filter_record(fields):
                        self.number_of_inserted_records += 1
                        new_records.append(self.transform_record(fields=fields, file=file))
            
            self.insert_data(new_records, cursor)
    

    def get_line_fields(self, line):
        """ Split a string `line` into a list of separate fields. """
        return line.split(self.separator)
    

    def parse_timestamp(self, timestamp):
        """
        Convert string timestamp into a datetime object with server timezone
        Append 3 trailing zeroes to parse fraction part as microseconds.
        
        This implementation is used in app access/event & scheduled db operations logs.
        """
        return datetime.strptime(timestamp + "000", "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=self.server_timezone)
    

    def filter_record(self, fields):
        """ 
        Return true if record `fields` should be added into the database or false otherwise.

        Default implementation attempts to run `parse_timestamp` on a field with `self.timestamp_field_number` number
        and check if it's inside the fetch period.
        """
        record_time = self.parse_timestamp(fields[self.timestamp_field_number])
        return self.min_time <= record_time <= self.max_time


    def transform_record(self, **kwargs):
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
