from spire.core import Dependency
from spire.mesh import MeshDependency
from spire.schema import SchemaDependency

from docket import resources
from docket.controllers.archetype import BaseArchetypeController
from docket.engine.archetype_registry import ArchetypeRegistry
from docket.models import *

class DocumentTypeController(BaseArchetypeController):
    resource = resources.DocumentType
    version = (1, 0)

    model = DocumentType
    mapping = 'id name designation description created modified resource properties'

    registry = Dependency(ArchetypeRegistry)
    schema = SchemaDependency('docket')
