from spire.schema import *

from docket.models.instance import Instance

__all__ = ('Constituent',)

schema = Schema('docket')

class Constituent(Instance):
    """A constituent."""

    class meta:
        polymorphic_identity = 'docket:constituent'
        schema = schema
        tablename = 'constituent'

    id = ForeignKey(Instance.id, nullable=False, primary_key=True)
