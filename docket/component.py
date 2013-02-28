from spire.core import Component, Dependency
from spire.exceptions import TemporaryStartupError
from spire.mesh import MeshDependency, MeshServer
from spire.runtime import onstartup
from spire.schema import SchemaDependency

import docket.models

from docket.bundles import *
#from docket.engine.archetype_registry import ArchetypeRegistry
from docket.engine.registry import EntityRegistry
from docket.resources import *

class Docket(Component):
    api = MeshServer.deploy(bundles=[API, DOCUMENT_API, INSTANCE_API])

    docket = MeshDependency('docket')
    platoon = MeshDependency('platoon')

    #archetype_registry = Dependency(ArchetypeRegistry)
    entity_registry = Dependency(EntityRegistry)

    @onstartup()
    def bootstrap(self):
        if not self.platoon.ping():
            raise TemporaryStartupError()

        self.entity_registry.bootstrap()
        #self.archetype_registry.bootstrap()
        self.api.server.configure_endpoints()
