from spire.schema import *

from docket.models.instance import Instance

__all__ = ('Document',)

schema = Schema('docket')

class Document(Instance):
    """A document."""

    class meta:
        polymorphic_identity = 'docket:document'
        schema = schema
        tablename = 'document'

    id = ForeignKey(Instance.id, nullable=False, primary_key=True)
