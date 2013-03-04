from mesh.standard import *
from scheme import *

from docket.resources.entity import BaseEntity
from docket.resources.instance import BaseInstance

class BaseDocument(Resource):
    """An entity document."""

    abstract = True
    version = 1

    class schema:
        id = UUID(oncreate=True, operators='equal')
