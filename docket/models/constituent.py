from spire.schema import *

from docket.models.entity import Entity

__all__ = ('Constituent',)

schema = Schema('docket')

class Constituent(Entity):
    """A constituent."""

    class meta:
        polymorphic_identity = 'docket:constituent'
        schema = schema
        tablename = 'constituent'

    id = ForeignKey(Entity.id, nullable=False, primary_key=True)
