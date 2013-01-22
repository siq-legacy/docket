from spire.schema import *

from docket.models.entity import Entity

schema = Schema('docket')

class Package(Entity):
    """A package of entities."""

    class meta:
        polymorphic_identity = 'docket:package'
        schema = schema
        tablename = 'package'

    is_container = True

    entity_id = ForeignKey(Entity.id, nullable=False, primary_key=True)
    package = Text()
