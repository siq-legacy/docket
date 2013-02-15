from mesh.standard import *
from scheme import *

__all__ = ('Registration',)

class Registration(Resource):
    """An entity registration."""

    name = 'registration'
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = Token(segments=2, nonempty=True, oncreate=True, operators='equal')
        name = Token(segments=1, nonempty=True, operators='equal')
        title = Text(nonempty=True, operators='equal')
        url = Text(nonempty=True)
        specification = Field(nonempty=True)
        is_container = Boolean(nonnull=True, default=False)
        canonical_version = Text()
        change_event = Token()
        cached_attributes = Map(Structure({
            'type': Token(segments=1, nonempty=True),
        }, nonnull=True), nonnull=True)

    class task:
        endpoint = ('TASK', 'registration')
        title = 'Initiating a registration task'
        schema = Structure(
            structure={
                'synchronize-entities': {},
            },
            nonempty=True,
            polymorphic_on=Enumeration(['synchronize-entities'],
                name='task', nonempty=True))
        responses = {
            OK: Response(),
            INVALID: Response(Errors),
        }
