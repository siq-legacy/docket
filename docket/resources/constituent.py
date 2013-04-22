from mesh.standard import *
from scheme import *

__all__ = ('BaseConstituent',)

class BaseConstituent(Resource):
    """An entity constituent."""

    abstract = True
    version = 1

    class schema:
        id = UUID(oncreate=True, operators='equal')
