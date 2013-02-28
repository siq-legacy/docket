from spire.schema import SchemaDependency

from docket import resources
from docket.controllers.entity import BaseEntityController
from docket.models import *

class IntentController(BaseEntityController):
    resource = resources.Intent
    version = (1, 0)

    model = Intent
    schema = SchemaDependency('docket')
    mapping = 'id name designation description created modified exclusive'
