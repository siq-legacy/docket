from mesh.standard import *
from scheme import *

class EntityBase(Resource):
    """Base aspects of an entity."""

    class schema:
        name = Text(nonempty=True, operators='equal contains icontains', annotational=True)
        designation = Text(operators='equal', annotational=True)
        description = Text(annotational=True)
        created = DateTime(utc=True, readonly=True, annotational=True)
        modified = DateTime(utc=True, readonly=True, annotational=True)
        containers = Sequence(Structure({
            'id': Text(nonempty=True),
            'entity': Token(segments=2, readonly=True),
            'name': Text(readonly=True),
        }, nonnull=True), nonnull=True, deferred=True, annotational=True)

class Entity(EntityBase):
    """An entity."""

    name = 'entity'
    version = 1
    requests = 'get query'

    class schema:
        id = Text(nonempty=True, operators='equal')
        entity = Token(segments=2)

    class task:
        endpoint = ('TASK', 'entity')
        title = 'Initiating an entity task'
