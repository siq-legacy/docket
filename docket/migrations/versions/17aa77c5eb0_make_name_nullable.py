"""make_name_nullable

Revision: 17aa77c5eb0
Revises: 35412f9eff96
Created: 2013-03-09 18:11:41.559446
"""

revision = '17aa77c5eb0'
down_revision = '35412f9eff96'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('entity', 'name', nullable=True)

def downgrade():
    op.alter_column('entity', 'name', nullable=False)
