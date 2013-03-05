"""remove_entity_test

Revision: 2dfd6f687af
Revises: None
Created: 2013-02-17 20:30:38.329327
"""

revision = '2dfd6f687af'
down_revision = None

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.execute('drop table if exists entity_test')

def downgrade():
    pass
