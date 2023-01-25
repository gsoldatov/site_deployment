"""
Script for fetching production server logs and inserting the into the local database.
"""
import argparse
from datetime import datetime

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from monitoring.log_fetching.jobs import job_list
from monitoring.util.config import get_config
from monitoring.util.logging import get_logger
from monitoring.util.util import check_internet_connection, get_local_tz


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
        help="Path to config file, relative to `monitoring` folder or absolute; default filename is `config.json`.")
    parser.add_argument("-j", "--jobs",
        help="A list of comma-separated job names to be run.")
    parser.add_argument("-f", "--min-time",
        help="Timestamp to update data from; uses 'YYYY-MM-DD_hh:mm:ss' format.")
    parser.add_argument("-t", "--max-time",
        help="Timestamp to update data to; uses 'YYYY-MM-DD_hh:mm:ss' format; if specified, -f option must be provided as well.")
    parser.add_argument("-F", "--force", default=False, action="store_true",
        help="Force script execution regardless of internet connection being metered or not.")
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
        if args.min_time > datetime.now().replace(tzinfo=local_tz):
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


def main():
    args = parse_args()
    log = get_logger()
    config = get_config(args.config)

    check_internet_connection(args.force, log)

    for job_name in args.jobs:
        Cls = job_list[job_name]
        job = Cls(job_name, args, config, log)
        job.run()


if __name__ == "__main__":
    main()
