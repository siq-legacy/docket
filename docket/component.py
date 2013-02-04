from spire.core import Component, Dependency
from spire.exceptions import TemporaryStartupError
from spire.mesh import MeshDependency, MeshServer
from spire.runtime import onstartup
from spire.schema import SchemaDependency

import docket.models

from docket.bundles import API
from docket.engine.registry import EntityRegistry
from docket.resources import *

class Docket(Component):
    api = MeshServer.deploy(bundles=[API])

    docket = MeshDependency('docket')
    platoon = MeshDependency('platoon')
    registry = Dependency(EntityRegistry)

    @onstartup()
    def bootstrap(self):
        if not self.platoon.ping():
            raise TemporaryStartupError()

        self.registry.bootstrap()
        self.api.server.configure_endpoints()
