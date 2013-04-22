from mesh.standard import *
from scheme import *

__all__ = ('Form',)

class Form(Resource):
    """A form specification."""

    name = 'form'
    version = 1
    requests = 'create delete get put query update'

    class schema:
        id = UUID(oncreate=True, operators='equal')
        title = Text()
        schema = Definition(nonempty=True)
        layout = Sequence(Structure({
            'title': Text(),
            'elements': Sequence(Structure({
                'type': Token(nonempty=True),
                'field': Token(nonempty=True),
                'label': Text(),
                'options': Field(),
            })),
        }), nonempty=True)
