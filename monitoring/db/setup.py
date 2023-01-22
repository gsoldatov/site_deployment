"""
A script for creating log database & user on a Postgresql server with the specified configuration.
"""
import argparse
import psycopg2

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from monitoring.config import get_config


def connect(config):
    host = config["db"]["db_host"]
    port = config["db"]["db_port"]
    database = config["db"]["db_init_database"]
    user = config["db"]["db_init_username"]
    password = config["db"]["db_init_password"]
    
    connection = psycopg2.connect(host=host, port=port, database=database, \
                            user=user, password=password)
    connection.set_session(autocommit=True)
    return connection


def setup_database(config):
    db_database = config["db"]["db_database"]
    db_username = config["db"]["db_username"]
    db_password = config["db"]["db_password"]

    connection = connect(config)
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_username}'")
        if not cursor.fetchone():
            cursor.execute(f"""CREATE ROLE {db_username} PASSWORD '{db_password}' LOGIN;""")
            print("Created user.")
        else:
            print("User already exists.")
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_database}'")
        if not cursor.fetchone():
            cursor.execute(f"""
                CREATE DATABASE {db_database} ENCODING 'UTF-8' 
                OWNER {db_username} TEMPLATE template0;
            """)
            print("Created database.")
        else:
            print("Database already exists.")
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
        help="Path to config file, relative to `monitoring` folder (one level above the folder of this script) or absolute; default filename is `config.json`")
    args = parser.parse_args()
    config = get_config(args.config)

    setup_database(config)


if __name__ == "__main__":
    main()
