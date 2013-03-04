from mesh.standard import *
from scheme import *

from docket.resources.archetype import BaseArchetype
from docket.resources.entity import BaseEntity

class DocumentType(Resource, BaseEntity[1], BaseArchetype[1]):
    """An entity archetype for documents."""

    name = 'documenttype'
    version = 1

    class schema:
        id = Token(nonempty=True, oncreate=True, operators='equal')
