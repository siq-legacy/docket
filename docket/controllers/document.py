from spire.schema import SchemaDependency

from docket.controllers.entity import BaseEntityController

class BaseDocumentController(BaseEntityController):
    schema = SchemaDependency('docket')
