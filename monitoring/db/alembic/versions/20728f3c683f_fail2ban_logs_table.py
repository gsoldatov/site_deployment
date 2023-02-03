"""fail2ban logs table

Revision ID: 20728f3c683f
Revises: 3a5ca57e6a5b
Create Date: 2023-02-03 17:49:44.206250

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import FetchedValue


# revision identifiers, used by Alembic.
revision = '20728f3c683f'
down_revision = '3a5ca57e6a5b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fail2ban_logs',
    sa.Column('record_id', sa.Integer(), server_default=FetchedValue(), nullable=False),
    sa.Column('record_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('event_type', sa.String(length=8), nullable=True),
    sa.Column('remote', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('record_id', name=op.f('pk_fail2ban_logs'))
    )
    op.create_index(op.f('ix_fail2ban_logs_record_time'), 'fail2ban_logs', ['record_time'], unique=False)
    # ### end Alembic commands ###

    op.execute("ALTER TABLE fail2ban_logs ALTER record_id ADD GENERATED BY DEFAULT AS IDENTITY")


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_fail2ban_logs_record_time'), table_name='fail2ban_logs')
    op.drop_table('fail2ban_logs')
    # ### end Alembic commands ###