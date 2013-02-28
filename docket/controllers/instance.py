from mesh.standard import OperationError
from spire.schema import SchemaDependency

from docket.controllers.entity import BaseEntityController

class BaseInstanceController(BaseEntityController):
    schema = SchemaDependency('docket')
