"""Nginx access logs table

Revision ID: e8f36d3ae355
Revises: 9c950c9dd9b4
Create Date: 2023-01-30 19:50:13.729993

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import FetchedValue


# revision identifiers, used by Alembic.
revision = 'e8f36d3ae355'
down_revision = '9c950c9dd9b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('nginx_access_logs',
    sa.Column('record_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('record_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('path', sa.Text(), nullable=True),
    sa.Column('method', sa.String(length=8), nullable=True),
    sa.Column('status', sa.SmallInteger(), nullable=True),
    sa.Column('body_bytes_sent', sa.Integer(), nullable=True),
    sa.Column('remote', sa.Text(), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('referer', sa.Text(), nullable=True),
    sa.Column('request', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('record_id', name=op.f('pk_nginx_access_logs'))
    )
    op.create_index(op.f('ix_nginx_access_logs_path'), 'nginx_access_logs', ['path'], unique=False)
    op.create_index(op.f('ix_nginx_access_logs_record_time'), 'nginx_access_logs', ['record_time'], unique=False)
    op.create_index(op.f('ix_nginx_access_logs_status'), 'nginx_access_logs', ['status'], unique=False)
    # ### end Alembic commands ###

    op.execute("ALTER TABLE nginx_access_logs ALTER record_id ADD GENERATED BY DEFAULT AS IDENTITY")


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_nginx_access_logs_status'), table_name='nginx_access_logs')
    op.drop_index(op.f('ix_nginx_access_logs_record_time'), table_name='nginx_access_logs')
    op.drop_index(op.f('ix_nginx_access_logs_path'), table_name='nginx_access_logs')
    op.drop_table('nginx_access_logs')
    # ### end Alembic commands ###
