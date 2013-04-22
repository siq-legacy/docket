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
