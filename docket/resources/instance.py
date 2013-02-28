from mesh.standard import *
from scheme import *

from docket.resources.entity import BaseEntity

class BaseInstance(Resource):
    """Bases aspects of an entity instance."""

    abstract = True
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = UUID(oncreate=True, operators='equal')

#class Instance(Resource, BaseEntity[1], BaseInstance[1]):
#    """An entity instance."""
#
#    name = 'instance'
#    version = 1
#
#    class schema:
#        archetype = Token(nonempty=True, operators='equal')
