"""add_standard_entities

Revision: 591141df4d22
Revises: 2dfd6f687af
Created: 2013-02-17 22:59:57.828582
"""

revision = '591141df4d22'
down_revision = '2dfd6f687af'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('registration', Column('standard_entities', JsonType(), nullable=True))

def downgrade():
    op.drop_column('registration', 'standard_entities')
