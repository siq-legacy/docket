from spire.schema import SchemaDependency

from docket.controllers.entity import BaseEntityController
from docket.models import *
from docket.resources.package import Package as PackageResource

class PackageController(BaseEntityController):
    resource = PackageResource
    version = (1, 0)

    model = Package
    schema = SchemaDependency('docket')
    mapping = 'id name designation description created modified package'
