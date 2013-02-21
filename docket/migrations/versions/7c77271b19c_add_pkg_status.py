"""add_pkg_status

Revision: 7c77271b19c
Revises: None
Created: 2013-02-21 08:59:44.930802
"""

revision = '7c77271b19c'
down_revision = '591141df4d22'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('package', Column('status', EnumerationType(), nullable=True))

def downgrade():
    op.drop_column('package', 'status')
