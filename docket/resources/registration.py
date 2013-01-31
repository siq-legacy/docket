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
        is_container = Boolean(nonnull=True, default=False)
        cached_attributes = Map(Structure({
            'type': Token(segments=1, nonempty=True),
        }, nonnull=True), nonnull=True)
        specification = Field(nonempty=True)
        canonical_version = Text()
