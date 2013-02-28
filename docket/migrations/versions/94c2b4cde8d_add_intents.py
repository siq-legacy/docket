"""add_intents

Revision: 94c2b4cde8d
Revises: 1cfe8fc19e87
Created: 2013-02-28 10:07:52.456022
"""

revision = '94c2b4cde8d'
down_revision = '1cfe8fc19e87'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('intent',
        Column('id', TextType(), nullable=False),
        Column('exclusive', BooleanType(), nullable=False),
        ForeignKeyConstraint(['id'], ['entity.id']),
        PrimaryKeyConstraint('id')
    )
    op.create_foreign_key('association_intent_fkey', 'association', 'intent', ['intent'], ['id'],
        ondelete='CASCADE')

def downgrade():
    op.drop_constraint('association_intent_fkey', 'association')
    op.drop_table('intent')
