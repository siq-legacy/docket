from mesh.standard import *
from scheme import *

class Item(Resource):
    """A contained entity."""

    name = 'item'
    version = 1

    class schema:
        id = Text(nonempty=True, operators='equal')
        entity = Token(segments=2, readonly=True)
        name = Text(readonly=True)

class BaseEntity(Resource):
    """Base aspects of an entity."""

    abstract = True
    version = 1

    class schema:
        name = Text(nonempty=True, operators='equal contains icontains', annotational=True)
        designation = Text(operators='equal', annotational=True)
        description = Text(annotational=True)
        created = DateTime(utc=True, readonly=True, annotational=True)
        modified = DateTime(utc=True, readonly=True, annotational=True)
        defunct = Boolean(operators='equal', readonly=True, annotational=True)
        containers = Sequence(Structure({
            'id': Text(nonempty=True),
            'entity': Token(segments=2, readonly=True),
            'name': Text(readonly=True),
        }, nonnull=True), nonnull=True, deferred=True, annotational=True)

class Entity(Resource, BaseEntity[1]):
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
        schema = Structure(
            structure={
                'synchronize-entities': {},
                'synchronize-entity': {
                    'id': UUID(nonempty=True),
                },
                'synchronize-changed-entity': {
                    'event': Structure({
                        'topic': Text(nonempty=True),
                        'id': UUID(nonempty=True),
                    }, nonnull=True, strict=False),
                },
            },
            nonempty=True,
            polymorphic_on=Enumeration(['synchronize-changed-entity', 'synchronize-entities',
                'synchronize-entity'], name='task', nonempty=True))
        responses = {
            OK: Response(),
            INVALID: Response(Errors),
        }
