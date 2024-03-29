from datetime import datetime

from mesh.standard import bind
from scheme import current_timestamp
from spire.core import Component, Dependency
from spire.exceptions import TemporaryStartupError
from spire.mesh import MeshDependency, MeshServer
from spire.runtime import current_runtime, onstartup
from spire.schema import Schema, SchemaDependency

from docket import models

from docket.bindings import platoon
from docket.bundles import BUNDLES
from docket.engine.archetype_registry import ArchetypeRegistry
from docket.engine.registry import EntityRegistry
from docket.resources import *

schema = Schema('docket')

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
    schema = SchemaDependency('docket')

    archetype_registry = Dependency(ArchetypeRegistry)
    entity_registry = Dependency(EntityRegistry)

    docket = MeshDependency('docket')
    platoon = MeshDependency('platoon')

    @onstartup()
    def bootstrap(self):
        self.entity_registry.bootstrap()
        self.archetype_registry.bootstrap()

        self.api.server.configure_endpoints()
        self.schema.purge()

    @onstartup(service='docket')
    def startup_docket(self):
        EVERY_SIX_HOURS.put()
        SYNC_ALL_ENTITIES.set_http_task(
            self.docket.prepare('docket/1.0/entity', 'task', None,
            {'task': 'synchronize-all-entities'}))
        SYNC_ALL_ENTITIES.put()

        self.entity_registry.subscribe_to_changes()
        return {'status': 'yielding', 'stage': 'dependents-ready'}

    @onstartup(service='docket', stage='dependents-ready')
    def restart_when_dependents_ready(self):
        current_runtime().reload()
        return {'status': 'restarting', 'stage': 'docket-ready'}

    @onstartup(service='docket', stage='docket-ready')
    def finish_docket_startup(self):
        self.entity_registry.synchronize_entities()
        return {'status': 'ready'}

@schema.constructor()
def bootstrap_documents(session):
    now = current_timestamp()
    matter = models.DocumentType(
        id='siq:matter',
        name='Matter',
        created=now,
        modified=now,
        resource='siq.matter')

    fileplan = models.DocumentType(
        id='siq:fileplan',
        name='File Plan',
        created=now,
        modified=now,
        resource='siq.fileplan')

    project = models.DocumentType(
        id='siq:project',
        name='Project',
        created=now,
        modified=now,
        resource='siq.project')

    available_to = models.Intent(
        id='available-to',
        name='Available to',
        created=now,
        modified=now,
        exclusive=False)

    contained_by = models.Intent(
        id='contained-by',
        name='Contained by',
        created=now,
        modified=now,
        exclusive=False)

    session.merge(matter)
    session.merge(fileplan)
    session.merge(project)
    session.merge(available_to)
    session.merge(contained_by)
    session.commit()
