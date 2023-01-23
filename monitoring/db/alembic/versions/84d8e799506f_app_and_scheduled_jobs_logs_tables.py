"""App and scheduled jobs logs tables

Revision ID: 84d8e799506f
Revises: 
Create Date: 2023-01-23 13:46:14.675852

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import FetchedValue


# revision identifiers, used by Alembic.
revision = '84d8e799506f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('app_access_logs',
    sa.Column('record_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('record_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('request_id', sa.String(length=8), nullable=True),
    sa.Column('path', sa.Text(), nullable=True),
    sa.Column('method', sa.String(length=8), nullable=True),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('elapsed_time', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('remote', sa.Text(), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('referer', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('record_id', name=op.f('pk_app_access_logs'))
    )
    op.create_index(op.f('ix_app_access_logs_path'), 'app_access_logs', ['path'], unique=False)
    op.create_index(op.f('ix_app_access_logs_record_time'), 'app_access_logs', ['record_time'], unique=False)
    op.create_index(op.f('ix_app_access_logs_request_id'), 'app_access_logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_app_access_logs_status'), 'app_access_logs', ['status'], unique=False)
    op.create_table('app_event_logs',
    sa.Column('record_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('record_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('request_id', sa.String(length=8), nullable=True),
    sa.Column('level', sa.String(length=8), nullable=True),
    sa.Column('event_type', sa.Text(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('details', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('record_id', name=op.f('pk_app_event_logs'))
    )
    op.create_index(op.f('ix_app_event_logs_record_time'), 'app_event_logs', ['record_time'], unique=False)
    op.create_index(op.f('ix_app_event_logs_request_id'), 'app_event_logs', ['request_id'], unique=False)
    op.create_table('database_scheduled_jobs_logs',
    sa.Column('record_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('job_type', sa.String(length=64), server_default=FetchedValue(), nullable=False),
    sa.Column('record_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('level', sa.String(length=8), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('record_id', 'job_type', name=op.f('pk_database_scheduled_jobs_logs'))
    )
    op.create_index(op.f('ix_database_scheduled_jobs_logs_record_time'), 'database_scheduled_jobs_logs', ['record_time'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_database_scheduled_jobs_logs_record_time'), table_name='database_scheduled_jobs_logs')
    op.drop_table('database_scheduled_jobs_logs')
    op.drop_index(op.f('ix_app_event_logs_request_id'), table_name='app_event_logs')
    op.drop_index(op.f('ix_app_event_logs_record_time'), table_name='app_event_logs')
    op.drop_table('app_event_logs')
    op.drop_index(op.f('ix_app_access_logs_status'), table_name='app_access_logs')
    op.drop_index(op.f('ix_app_access_logs_request_id'), table_name='app_access_logs')
    op.drop_index(op.f('ix_app_access_logs_record_time'), table_name='app_access_logs')
    op.drop_index(op.f('ix_app_access_logs_path'), table_name='app_access_logs')
    op.drop_table('app_access_logs')
    # ### end Alembic commands ###
