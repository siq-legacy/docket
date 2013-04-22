from spire.mesh import Definition
from spire.schema import *

__all__ = ('Form',)

schema = Schema('docket')

class Form(Model):
    """A dynamic form."""

    class meta:
        schema = schema
        tablename = 'form'

    id = Identifier()
    title = Text()
    schema = Definition(nullable=False)
    layout = Json(nullable=False)
