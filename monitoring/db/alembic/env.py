from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import urllib.parse

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from monitoring.util.config import get_config
from monitoring.db.tables import get_tables


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get monitoring config
x_arguments = context.get_x_argument(as_dictionary=True)
monitoring_config = x_arguments.get("monitoring_config")
if monitoring_config is not None:
    monitoring_config = monitoring_config.replace('"', '')
mc = get_config(monitoring_config)

# Set connection string
username = urllib.parse.quote(mc["db"]["db_username"]).replace("%", "%%") # encode special characters in username and password;
password = urllib.parse.quote(mc["db"]["db_password"]).replace("%", "%%") # after quoting, '%' chars must also be escaped to avoid "ValueError: invalid interpolation syntax" exception

config.set_main_option("sqlalchemy.url", f"postgresql://{username}:{password}"
                        f"@{mc['db']['db_host']}:{mc['db']['db_port']}/{mc['db']['db_database']}")


# Add model's MetaData
target_metadata = get_tables()[1]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Default function for applying migrations; requires psycopg2 instead of psycopg
def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
