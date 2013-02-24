from mesh.standard import *
from scheme import *

class Association(Resource):
    """An entity association."""

    name = 'association'
    version = 1
    composite_key = 'subject intent target'
    requests = 'delete put query'

    class schema:
        id = Text(oncreate=True, operators='equal')
        subject = Token(nonempty=True, operators='equal')
        intent = Token(nonempty=True, operators='equal')
        target = Token(nonempty=True, operators='equal')
