"""add_associations

Revision: 1cfe8fc19e87
Revises: 7c77271b19c
Created: 2013-02-24 16:33:37.077231
"""

revision = '1cfe8fc19e87'
down_revision = '7c77271b19c'

from alembic import op
from spire.schema.fields import *
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('association',
        Column('subject_id', TextType(), nullable=False),
        Column('intent', TokenType(), nullable=False),
        Column('target_id', TextType(), nullable=False),
        ForeignKeyConstraint(['subject_id'], ['entity.id'], ),
        ForeignKeyConstraint(['target_id'], ['entity.id'], ),
        PrimaryKeyConstraint('subject_id', 'intent', 'target_id')
    )
    op.drop_table(u'container_membership')

def downgrade():
    op.create_table(u'container_membership',
        Column(u'container_id', TextType(), nullable=False),
        Column(u'member_id', TextType(), nullable=False),
        ForeignKeyConstraint(['container_id'], [u'entity.id'], name=u'container_membership_container_id_fkey'),
        ForeignKeyConstraint(['member_id'], [u'entity.id'], name=u'container_membership_member_id_fkey'),
        PrimaryKeyConstraint(u'container_id', u'member_id', name=u'container_membership_pkey')
    )
    op.drop_table('association')
