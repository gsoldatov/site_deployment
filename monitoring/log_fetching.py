"""
Script for fetching production server logs and inserting the into the local database.
"""
import argparse
from datetime import datetime
import subprocess
import traceback
from uuid import uuid4

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from monitoring.log_fetching.jobs import job_list, JobAborted
from monitoring.util.config import get_config
from monitoring.util.logging import PrintLogger, DatabaseLogger
from monitoring.util.util import get_current_time, get_local_tz
from monitoring.db.util import connect


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--env-file",
        help="Path to file with environment variables, relative to `ansible` folder or absolute; default filename is `production.env`.")
    parser.add_argument("-j", "--jobs",
        help="A list of comma-separated job names to be run.")
    parser.add_argument("-f", "--min-time",
        help="Timestamp to update data from; uses 'YYYY-MM-DD_hh:mm:ss' format.")
    parser.add_argument("-t", "--max-time",
        help="Timestamp to update data to; uses 'YYYY-MM-DD_hh:mm:ss' format; if specified, -f option must be provided as well.")
    parser.add_argument("-F", "--force", default=False, action="store_true",
        help="Force script execution regardless of internet connection being metered or not.")
    parser.add_argument("--full-fetch", default=False, action="store_true",
        help="Fetch all existing files from the server and override the fetch period based on their content.")
    args = parser.parse_args()

    # Parse --min-time & --max-time
    if args.max_time and args.min_time is None:
        parser.error("--max-time option requires --min-time option to be passed as well.")
    
    local_tz = get_local_tz()

    for attr in ("min_time", "max_time"):
        val = getattr(args, attr, None)
        if val:
            try:
                d = datetime.strptime(val, "%Y-%m-%d_%H:%M:%S")
                d = d.replace(tzinfo=local_tz)
                setattr(args, attr, d)
            except ValueError:
                parser.error(f"--{attr} must be in 'YYYY-MM-DD_hh:mm:ss' format.")
    
    if args.min_time:
        if args.min_time > get_current_time():
            parser.error("--min-time cannot be greater than current time")
        
        if args.max_time:
            if args.min_time >= args.max_time:
                parser.error("--min-time must be < --max-time")
    
    # Parse --jobs or set default value
    if args.jobs is None:
        args.jobs = [job for job in job_list.keys()]
    else:
        args.jobs = args.jobs.split(",")
        for job in args.jobs:
            if job not in job_list:
                parser.error(f"Invalid job name: '{job}'")
    
    return args


class JobRunner:
    def __init__(self):
        self.args = parse_args()
        self.config = get_config(self.args.env_file)
        self.execution_id = str(uuid4())[:8]

        self.db_connection = connect(self.config, db="logs")
        
        if self.config["logging_mode"] == "stdout":
            self._logger = PrintLogger()
        elif self.config["logging_mode"] == "db":
            self._logger = DatabaseLogger(self.db_connection)
    

    def log(self, job_name, level, message):
        self._logger.log(record_time=get_current_time(), execution_id=self.execution_id,
            job_name=job_name, level=level, message=message)
    

    def is_internet_connection_available(self):
        """
        Returns true if a non-metered Internet connection is available or 
        a metered connection is available and --force flag is passed.
        """
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ansible/roles/deployment_management_setup_backup/scripts/util.sh"))
        cmd = f"bash -c \"source '{script_path}'; is_metered_connection\"" # bash interpreter is required to correctly source the function
                                                                        # subprocess uses /bin/sh, which may be linked to dash
        proc = subprocess.Popen(cmd, shell=True)
        proc.communicate()

        if proc.returncode == 2: self.log("main", "WARNING", "No internet connection available."); return False
        elif proc.returncode == 1 and not self.args.force: self.log("main", "WARNING", "Internet connection is metered."); return False
        return True
    

    def update_fetch_job_status(self, job_name, last_execution_status, 
        last_execution_time, last_successful_full_fetch_time = None):
        """ Update the status of the job in the database when it's finished. """

        with self.db_connection:
            with self.db_connection.cursor() as cursor:
                # Update `last_successful_full_fetch_time` value, if it's provided
                if last_successful_full_fetch_time:
                    cursor.execute("""
                        INSERT INTO fetch_jobs_status (job_name, last_execution_id, last_execution_status, last_execution_time, last_successful_full_fetch_time)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (job_name) DO UPDATE
                        SET job_name = EXCLUDED.job_name, last_execution_id = EXCLUDED.last_execution_id, last_execution_status = EXCLUDED.last_execution_status,
                            last_execution_time = EXCLUDED.last_execution_time, last_successful_full_fetch_time = EXCLUDED.last_successful_full_fetch_time
                    """, [job_name, self.execution_id, last_execution_status, last_execution_time, last_successful_full_fetch_time])
                
                else:
                    # If no `last_successful_full_fetch_time` provided, do not update existing value (or insert null)
                    cursor.execute("""
                        INSERT INTO fetch_jobs_status (job_name, last_execution_id, last_execution_status, last_execution_time)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (job_name) DO UPDATE
                        SET job_name = EXCLUDED.job_name, last_execution_id = EXCLUDED.last_execution_id, last_execution_status = EXCLUDED.last_execution_status,
                            last_execution_time = EXCLUDED.last_execution_time
                    """, [job_name, self.execution_id, last_execution_status, last_execution_time])
    

    def run(self):
        # Check if internet connection is available
        if not self.is_internet_connection_available():
            now = get_current_time()
            for job_name in self.args.jobs:
                self.update_fetch_job_status(job_name, "no connection", now)
            return
        
        # Run jobs
        try:
            for job_name in self.args.jobs:
                try:
                    now = get_current_time()
                    Cls = job_list[job_name]
                    job = Cls(job_name, self.args, self.config, self.db_connection, self.log)
                    job.run()

                    if getattr(job, "full_fetch", None):
                        last_successful_full_fetch_time = now if job.full_fetch else None
                    else:
                        last_successful_full_fetch_time = now
                    self.update_fetch_job_status(job_name, "success", now, last_successful_full_fetch_time=last_successful_full_fetch_time)
                except JobAborted:
                    self.update_fetch_job_status(job_name, "failed", now)
                except Exception as e:
                    self.log(job_name, "ERROR", traceback.format_exc())
                    raise
        
        except:
            self.update_fetch_job_status(job_name, "failed", now)
            raise
        
        finally:
            self._logger.flush()
            self.db_connection.close()



def main():
    job_runner = JobRunner()
    job_runner.run()    


if __name__ == "__main__":
    main()
