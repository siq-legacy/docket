from mesh.standard import *
from scheme import *

class BaseDocument(Resource):
    """An entity document."""

    abstract = True
    version = 1

    class schema:
        id = UUID(oncreate=True, operators='equal')
