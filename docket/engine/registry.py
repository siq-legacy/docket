import re
import uuid

from mesh.standard import Resource, bind
from spire.core import Unit
from spire.mesh import MeshDependency
from spire.runtime import current_runtime
from spire.schema import *
from spire.support.logs import LogHelper
from spire.util import nsuniqid
from sqlalchemy import MetaData
from sqlalchemy.orm import undefer

from docket.bindings import platoon
from docket.engine.annotation import Annotator
from docket.models import Entity, Registration

TASK_UUID_NAMESPACE = uuid.UUID('49be9141-1865-4d33-872b-b5a0b34b3017')

log = LogHelper('docket')
ScheduledTask = bind(platoon, 'platoon/1.0/scheduledtask')
SubscribedTask = bind(platoon, 'platoon/1.0/subscribedtask')

class EntityRegistry(Unit):
    """The entity registry."""

    docket = MeshDependency('docket')
    platoon = MeshDependency('platoon')
    schema = SchemaDependency('docket')

    def __init__(self):
        self.proxies = {}
        self.annotator = Annotator(self.proxies)
        self.models = {}

    def bootstrap(self):
        from docket.bundles import ENTITY_API
        session = self.schema.session

        for registration in session.query(Registration).options(undefer('specification')):
            model = self.models[registration.id] = self._construct_model(registration)

            self.annotator.process(registration, model)
            if registration.change_event:
                self._subscribe_to_changes(registration)

        session.commit()
        ENTITY_API.attach(self.annotator.generate_mounts())

    def get_proxy(self, id, version):
        return self.proxies['%s:%s' % (id, version)]

    def synchronize_entities(self):
        session = self.schema.session
        Entity.synchronize_entities(self, session)

    def unregister(self, registration):
        table = self._construct_table(registration)
        if self.schema.table_exists(table):
            self.schema.drop_table(table)

    def _construct_model(self, registration):
        attrs = {'entity_id': ForeignKey('entity.id', nullable=False, primary_key=True)}
        for name, attr in sorted(registration.cached_attributes.iteritems()):
            attrs[name] = attr.contribute_field()

        tablename = self._prepare_tablename(registration.id)
        model = self.schema.construct_model(Entity, tablename, attrs, registration.title,
            polymorphic_identity=registration.id)

        registration.annotate(model)
        self.schema.create_or_update_table(model.__table__)
        return model

    def _construct_table(self, registration):
        metadata = MetaData()
        entities = Table('entity', metadata, Text(name='id', nullable=False, primary_key=True))

        tablename = self._prepare_tablename(registration.id)
        table = Table(tablename, metadata,
            ForeignKey(name='entity_id', column=entities.c.id, type_=TextType(),
                nullable=False, primary_key=True))

        for name, attr in sorted(registration.cached_attributes.iteritems()):
            table.append_column(attr.contribute_field())

        return table

    def _prepare_tablename(self, id):
        tablename = id.lower().replace(':', '_')
        return 'entity_' + re.sub(r'[^a-z_]', '', tablename).strip('_')

    def _subscribe_to_changes(self, registration):
        task = self.docket.prepare('docket/1.0/entity', 'task', None,
            {'task': 'synchronize-changed-entity'})

        task['injections'] = ['event']
        SubscribedTask(
            id=nsuniqid(TASK_UUID_NAMESPACE, registration.id),
            tag='%s changes' % registration.id,
            topic=registration.change_event,
            task=SubscribedTask.prepare_http_task(task)).put()
