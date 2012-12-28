from mesh.standard import *
from scheme import *

class Entity(Resource):
    """An entity."""

    name = 'entity'
    version = 1

    class schema:
        id = Text(nonempty=True, operators='equal')
        entity = Token(segments=2)
        name = Text(nonempty=True, operators='contains icontains', annotational=True)
        designation = Text(operators='equal', annotational=True)
        description = Text(annotational=True)
        created = DateTime(utc=True, readonly=True, annotational=True)
        modified = DateTime(utc=True, readonly=True, annotational=True)

    class task:
        endpoint = ('TASK', 'entity')
        title = 'Initiating an entity task'
