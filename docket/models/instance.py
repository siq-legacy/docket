from spire.schema import *

from docket.models.entity import Entity

__all__ = ('Instance',)

schema = Schema('docket')

class Instance(Entity):
    """An archetype instance."""
    
    class meta:
        polymorphic_identity = 'docket:instance'
        schema = schema
        tablename = 'instance'

    id = ForeignKey(Entity.id, nullable=False, primary_key=True)
