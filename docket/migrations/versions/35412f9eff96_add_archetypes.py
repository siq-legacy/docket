"""add_archetypes

Revision: 35412f9eff96
Revises: 94c2b4cde8d
Created: 2013-03-04 10:43:31.257915
"""

revision = '35412f9eff96'
down_revision = '94c2b4cde8d'

from alembic import op
from spire.schema.fields import *
from spire.mesh import DefinitionType
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('archetype',
        Column('entity_id', TextType(), nullable=False),
        Column('resource', TokenType(), nullable=False),
        Column('properties', DefinitionType(), nullable=True),
        ForeignKeyConstraint(['entity_id'], ['entity.id']),
        PrimaryKeyConstraint('entity_id')
    )
    op.create_table('instance',
        Column('id', TextType(), nullable=False),
        ForeignKeyConstraint(['id'], ['entity.id']),
        PrimaryKeyConstraint('id')
    )
    op.create_table('document',
        Column('id', TextType(), nullable=False),
        ForeignKeyConstraint(['id'], ['instance.id']),
        PrimaryKeyConstraint('id')
    )
    op.create_table('documenttype',
        Column('archetype_id', TextType(), nullable=False),
        ForeignKeyConstraint(['archetype_id'], ['archetype.entity_id']),
        PrimaryKeyConstraint('archetype_id')
    )

def downgrade():
    op.drop_table('documenttype')
    op.drop_table('document')
    op.drop_table('instance')
    op.drop_table('archetype')
