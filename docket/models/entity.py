from scheme import current_timestamp
from spire.schema import *
from spire.support.logs import LogHelper

log = LogHelper('docket')
schema = Schema('docket')

ContainerMembership = Table('container_membership', schema.metadata,
    ForeignKey(name='container_id', column='entity.id', nullable=False, primary_key=True),
    ForeignKey(name='member_id', column='entity.id', nullable=False, primary_key=True))

class Entity(Model):
    """An entity."""

    class meta:
        polymorphic_on = 'entity'
        schema = schema
        tablename = 'entity'

    id = Text(nullable=False, primary_key=True)
    entity = Token(nullable=False, index=True)
    name = Text(nullable=False, index=True)
    designation = Text(index=True)
    description = Text()
    created = DateTime(timezone=True, nullable=False)
    modified = DateTime(timezone=True, nullable=False)

    containers = relationship('Entity', secondary=ContainerMembership,
        backref=backref('members'),
        primaryjoin=(id==ContainerMembership.c.member_id),
        secondaryjoin=(id==ContainerMembership.c.container_id))

    is_container = False

class TestEntity(Entity):
    class meta:
        polymorphic_identity = 'docket:test'
        schema = schema
        tablename = 'entity_test'

    entity_id = ForeignKey('entity.id', nullable=False, primary_key=True)

