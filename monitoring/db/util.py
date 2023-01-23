import psycopg2


def connect(config, db):
    """
    Returns a connection object to the initial or log database.
    """
    host = config["db"]["db_host"]
    port = config["db"]["db_port"]
    database = config["db"]["db_init_database"] if db == "initial" else config["db"]["db_database"]
    user = config["db"]["db_init_username"] if db == "initial" else config["db"]["db_username"]
    password = config["db"]["db_init_password"] if db == "initial" else config["db"]["db_password"]

    connection = psycopg2.connect(host=host, port=port, database=database, \
                            user=user, password=password)

    if db == "initial":
        connection.set_session(autocommit=True)
    
    return connection
