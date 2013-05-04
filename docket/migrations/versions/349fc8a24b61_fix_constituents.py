"""fix_constituents

Revision: 349fc8a24b61
Revises: 3a760a7c053c
Created: 2013-04-25 14:40:20.550672
"""

revision = '349fc8a24b61'
down_revision = '3a760a7c053c'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_constraint('constituent_id_fkey', 'constituent')
    op.create_foreign_key('constituent_id_fkey', 'constituent', 'entity', ['id'], ['id'])

def downgrade():
    op.drop_constraint('constituent_id_fkey', 'constituent')
    op.create_foreign_key('constituent_id_fkey', 'constituent', 'instance', ['id'], ['id'])
