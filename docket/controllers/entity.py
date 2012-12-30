from spire.mesh import ModelController
from spire.schema import SchemaDependency

from docket.models import *
from docket.resources import Entity as EntityResource

class EntityController(ModelController):
    resource = EntityResource
    version = (1, 0)

    model = Entity
    schema = SchemaDependency('docket')
    mapping = 'id entity name designation description created modified'

