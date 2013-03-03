from spire.core import Component, Dependency
from spire.exceptions import TemporaryStartupError
from spire.mesh import MeshDependency, MeshServer
from spire.runtime import current_runtime, onstartup
from spire.schema import SchemaDependency

import docket.models

from docket.bundles import BUNDLES
#from docket.engine.archetype_registry import ArchetypeRegistry
from docket.engine.registry import EntityRegistry
from docket.resources import *

class Docket(Component):
    api = MeshServer.deploy(bundles=BUNDLES)

    #archetype_registry = Dependency(ArchetypeRegistry)
    entity_registry = Dependency(EntityRegistry)

    @onstartup()
    def bootstrap(self):
        self.entity_registry.bootstrap()
        #self.archetype_registry.bootstrap()
        self.api.server.configure_endpoints()

    @onstartup(service='docket')
    def startup_docket(self):
        # set up platoon tasks
        return {'status': 'yielding', 'stage': 'dependents-ready'}

    @onstartup(service='docket', stage='dependents-ready')
    def restart_when_dependents_ready(self):
        current_runtime().reload()
        return {'status': 'restarting', 'stage': 'docket-ready'}

    @onstartup(service='docket', stage='docket-ready')
    def finish_docket_startup(self):
        self.entity_registry.synchronize_entities()
        return {'status': 'ready'}

