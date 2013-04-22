from mesh.standard import *
from scheme import *

from docket.resources.entity import BaseEntity

class BaseArchetype(Resource):
    """Base aspects of an entity archetype."""

    abstract = True
    version = 1

    class schema:
        resource = Token(segments=1, nonempty=True)
        properties = Definition()

class Archetype(Resource, BaseEntity[1], BaseArchetype[1]):
    """An entity archetype."""

    name = 'archetype'
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = Token(nonempty=True, oncreate=True, operators='equal')
