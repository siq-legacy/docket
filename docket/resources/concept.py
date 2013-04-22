from mesh.standard import *
from scheme import *

from docket.resources.archetype import BaseArchetype
from docket.resources.entity import BaseEntity

__all__ = ('Concept',)

class Concept(Resource, BaseEntity[1], BaseArchetype[1]):
    """An entity archetype for concepts."""

    name = 'concept'
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = Token(nonempty=True, oncreate=True, operators='equal')
