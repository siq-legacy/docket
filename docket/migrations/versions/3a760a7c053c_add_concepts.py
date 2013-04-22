"""add_concepts

Revision: 3a760a7c053c
Revises: 17aa77c5eb0
Created: 2013-04-22 14:15:39.071110
"""

revision = '3a760a7c053c'
down_revision = '17aa77c5eb0'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('constituent',
        Column('id', TextType(), nullable=False),
        ForeignKeyConstraint(['id'], ['instance.id'], ),
        PrimaryKeyConstraint('id')
    )
    op.create_table('concept',
        Column('archetype_id', TextType(), nullable=False),
        ForeignKeyConstraint(['archetype_id'], ['archetype.entity_id'], ),
        PrimaryKeyConstraint('archetype_id')
    )

def downgrade():
    op.drop_table('concept')
    op.drop_table('constituent')
