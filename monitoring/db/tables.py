from sqlalchemy import (
    MetaData, Table, Column, DateTime, Integer, 
    SmallInteger, Float, String, Text
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
        "app_access_log": Table(
            "app_access_log",
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

        "app_event_log": Table(
            "app_event_log",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("request_id", String(8), index=True),
            Column("level", String(8)),
            Column("event_type", Text),
            Column("message", Text),
            Column("details", Text)
        ),

        "database_scheduled_jobs": Table(
            "database_scheduled_jobs",
            meta,
            Column("record_id", Integer, primary_key=True, server_default=FetchedValue()),
            Column("job_type", String(64), primary_key=True, server_default=FetchedValue()),
            Column("record_time", DateTime(timezone=True), nullable=False, index=True),
            Column("level", String(8)),
            Column("message", Text)
        )
    } \
    , meta
