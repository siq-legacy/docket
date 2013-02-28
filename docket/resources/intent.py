from mesh.standard import *
from scheme import *

from docket.resources.entity import BaseEntity

class Intent(Resource, BaseEntity[1]):
    """An association intent."""

    name = 'intent'
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = Token(segments=1, oncreate=True, operators='equal')
        exclusive = Boolean(default=False, operators='equal')
