"""add_forms

Revision: 3ed458a8ac10
Revises: 17aa77c5eb0
Created: 2013-04-22 11:13:03.569848
"""

revision = '3ed458a8ac10'
down_revision = '17aa77c5eb0'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('form',
        Column('id', UUIDType(), nullable=False),
        Column('title', TextType(), nullable=True),
        Column('schema', DefinitionType(), nullable=False),
        Column('layout', JsonType(), nullable=False),
        PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('form')
