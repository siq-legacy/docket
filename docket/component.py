from datetime import datetime

from mesh.standard import bind
from spire.core import Component, Dependency
from spire.exceptions import TemporaryStartupError
from spire.mesh import MeshDependency, MeshServer
from spire.runtime import current_runtime, onstartup
from spire.schema import SchemaDependency

import docket.models

from docket.bindings import platoon
from docket.bundles import BUNDLES
#from docket.engine.archetype_registry import ArchetypeRegistry
from docket.engine.registry import EntityRegistry
from docket.resources import *

RecurringTask = bind(platoon, 'platoon/1.0/recurringtask')
Schedule = bind(platoon, 'platoon/1.0/schedule')

EVERY_SIX_HOURS = Schedule(
    id='c53628ff-7b48-4f60-ba56-bea431fc7da2',
    name='every six hours',
    schedule='fixed',
    anchor=datetime(2000, 1, 1, 0, 0, 0),
    interval=21600)

SYNC_ALL_ENTITIES = RecurringTask(
    id='7d715e10-0f00-476d-ace1-dc896d7da3e5',
    tag='synchronize-all-entities',
    schedule_id=EVERY_SIX_HOURS.id,
    retry_limit=0)

class Docket(Component):
    api = MeshServer.deploy(bundles=BUNDLES)

    #archetype_registry = Dependency(ArchetypeRegistry)
    entity_registry = Dependency(EntityRegistry)

    docket = MeshDependency('docket')
    platoon = MeshDependency('platoon')

    @onstartup()
    def bootstrap(self):
        self.entity_registry.bootstrap()
        #self.archetype_registry.bootstrap()
        self.api.server.configure_endpoints()

    @onstartup(service='docket')
    def startup_docket(self):
        EVERY_SIX_HOURS.put()
        SYNC_ALL_ENTITIES.set_http_task(
            self.docket.prepare('docket/1.0/entity', 'task', None,
            {'task': 'synchronize-all-entities'}))
        SYNC_ALL_ENTITIES.put()

        return {'status': 'yielding', 'stage': 'dependents-ready'}

    @onstartup(service='docket', stage='dependents-ready')
    def restart_when_dependents_ready(self):
        current_runtime().reload()
        return {'status': 'restarting', 'stage': 'docket-ready'}

    @onstartup(service='docket', stage='docket-ready')
    def finish_docket_startup(self):
        self.entity_registry.synchronize_entities()
        return {'status': 'ready'}

