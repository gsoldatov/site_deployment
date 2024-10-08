"""
A script for creating log database & user on a Postgresql server with the specified configuration.
"""
import argparse

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from monitoring.db.util import connect
from monitoring.util.config import get_config
from monitoring.util.logging import PrintLogger


logger = PrintLogger()


def setup_database(config):
    db_database = config["db"]["db_database"]
    db_username = config["db"]["db_username"]
    db_password = config["db"]["db_password"]

    connection = connect(config, db="initial")
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_username}'")
        if not cursor.fetchone():
            cursor.execute(f"""CREATE ROLE {db_username} PASSWORD '{db_password}' LOGIN;""")
            logger.log(message="Created user.")
        else:
            logger.log(message="User already exists.")
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_database}'")
        if not cursor.fetchone():
            cursor.execute(f"""
                CREATE DATABASE {db_database} ENCODING 'UTF-8' 
                OWNER {db_username} TEMPLATE template0;
            """)
            logger.log(message="Created database.")
        else:
            logger.log(message="Database already exists.")
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--env-file",
        help="Path to env file, absolute or relative to `ansible` folder; default filename is `production.env`")
    args = parser.parse_args()
    config = get_config(args.env_file)

    setup_database(config)


if __name__ == "__main__":
    main()
