from spire.schema import *

from docket import resources
from docket.models.archetype import Archetype
from docket.models.document import Document
from docket.resources.entity import BaseEntity
from docket.resources.instance import BaseInstance
from docket.resources.document import BaseDocument

__all__ = ('DocumentType',)

schema = Schema('docket')

class DocumentType(Archetype):
    """A document type."""

    class meta:
        polymorphic_identity = 'docket:documenttype'
        schema = schema
        tablename = 'documenttype'

    class config:
        bundle = 'docket.DOCUMENT_API'
        model = Document
        prefix = 'document'
        resources = [
            ((1, 0), (BaseDocument[1], BaseInstance[1], BaseEntity[1]),
                'docket.controllers.document.BaseDocumentController'),
        ]

    archetype_id = ForeignKey(Archetype.entity_id, nullable=False, primary_key=True)
