from sqlalchemy import (
    MetaData, Table, Column, Index, DateTime, Integer, BigInteger,
    Date, SmallInteger, Float, String, Text, Boolean
)
from sqlalchemy.schema import FetchedValue


def get_tables():
    """ Return a dictionary with SA tables and a metadata object. """
    meta = MetaData(naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

    return {
        # Fetch script staus & logs
        "fetch_jobs_status": Table(
            "fetch_jobs_status",
            meta,
            Column("job_name", String(32), primary_key=True),
            Column("last_execution_id", String(8)),
            Column("last_execution_status", String(32), nullable=False),
            Column("last_execution_time", DateTime(timezone=True), nullable=False),
            Column("last_successful_full_fetch_time", DateTime(timezone=True))
        ),

        "fetch_jobs_logs": Table(
            "fetch_jobs_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("execution_id", String(8)),
            Column("job_name", String(32)),
            Column("level", String(8)),
            Column("message", Text)
        ),

        # Healthcheck table
        "healthcheck": Table(
            "healthcheck",
            meta,
            Column("execution_time", DateTime(timezone=True)),
            Column("server_reachable", Boolean),
            Column("nginx_status", Text),
            Column("backend_status", Text),
            Column("postgresql_status", Text),
            Column("cpu_usage", Float),
            Column("memory_used", BigInteger),
            Column("memory_available", BigInteger),
            Column("memory_swap", BigInteger),
            Column("memory_total", BigInteger),
            Column("disk_used", BigInteger),
            Column("disk_total", BigInteger),
            Column("ssl_expiry_time", DateTime(timezone=True))
        ),

        # Remote log tables
        "app_access_logs": Table(
            "app_access_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("request_id", String(8), index=True),
            Column("path", Text, index=True),
            Column("method", String(8)),
            Column("status", SmallInteger, index=True),
            Column("elapsed_time", Float),
            Column("user_id", Integer),
            Column("remote", Text),
            Column("user_agent", Text),
            Column("referer", Text)
        ),

        "app_event_logs": Table(
            "app_event_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("request_id", String(8), index=True),
            Column("level", String(8)),
            Column("event_type", Text),
            Column("message", Text),
            Column("details", Text)
        ),

        "database_scheduled_jobs_logs": Table(
            "database_scheduled_jobs_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("job_type", String(64), index=True, nullable=False),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("level", String(8)),
            Column("message", Text)
        ),

        "nginx_access_logs": Table(
            "nginx_access_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("path", Text, index=True),
            Column("method", String(8)),
            Column("status", SmallInteger, index=True),
            Column("body_bytes_sent", Integer),
            Column("remote", Text),
            Column("user_agent", Text),
            Column("referer", Text),
            Column("request", Text)
        ),

        "nginx_error_logs": Table(
            "nginx_error_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("level", String(8)),
            Column("message", Text)
        ),

        "server_auth_logs": Table(
            "server_auth_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("ut_type", SmallInteger),
            Column("user", Text),
            Column("remote", Text)
        ),

        "known_ips": Table(
            "known_ips",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("login_date", Date, nullable=False, index=True),
            Column("remote", Text),
            Index("ix_known_ips_remote_login_date", "remote", "login_date", unique=True)
        ),

        "fail2ban_logs": Table(
            "fail2ban_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("event_type", String(8)),
            Column("remote", Text)
        ),

        # Local log tables
        "backup_script_logs": Table(
            "backup_script_logs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("level", String(8)),
            Column("event_source", String(32)),
            Column("message", Text)
        )
    } \
    , meta
