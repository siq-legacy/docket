import re

import scheme
from mesh.bundle import mount
from mesh.standard import Resource, bind
from spire.core import Unit
from spire.mesh import MeshDependency
from spire.runtime import current_runtime
from spire.schema import *
from spire.support.logs import LogHelper
from spire.util import import_object
from sqlalchemy import MetaData

from docket import resources
from docket.bindings import platoon
from docket.models import *

log = LogHelper('docket')

PROTOTYPES = (DocumentType,)

class ArchetypeRegistry(Unit):
    """The archetype registry."""

    schema = SchemaDependency('docket')

    def __init__(self):
        self.models = {}

    def bootstrap(self):
        session = self.schema.session
        for prototype in PROTOTYPES:
            self._bootstrap_prototype(session, prototype)

        session.commit()

    def register(self, archetype, changed=False):
        table = self._construct_table(archetype)
        if changed or not self.schema.is_table_correct(table):
            current_runtime().reload()

    def unregister(self, archetype):
        table = self._construct_table(archetype)
        if self.schema.table_exists(table):
            self.schema.drop_table(table)
            current_runtime().reload()

    def _bootstrap_prototype(self, session, prototype):
        bundle = import_object(prototype.config.bundle)
        for archetype in session.query(prototype):
            model = self.models[archetype.id] = self._construct_model(archetype)
            bundle.attach([self._construct_mount(archetype, model)])

    def _construct_controller(self, model, resource, version, controller, mixin_controller):
        bases = (mixin_controller, controller) if controller else (mixin_controller,)
        return type('%sController' % resource.title, bases, {
            'model': model,
            'resource': resource,
            'version': version,
        })

    def _construct_model(self, archetype):
        parent = archetype.config.model
        attrs = {'id': ForeignKey(parent.id, nullable=False, primary_key=True)}

        tablename = self._prepare_tablename(archetype.config.prefix, archetype.id)
        model = self.schema.construct_model(parent, tablename, attrs, tablename,
            polymorphic_identity=archetype.id)

        self.schema.create_or_update_table(model.__table__)
        return model

    def _construct_mount(self, archetype, model):
        resource = Resource
        controller = None

        for version, mixins, mixin_controller in archetype.config.resources:
            if resource.version != version[0]:
                resource = self._construct_resource(archetype, resource, version[0], mixins)

            controller = self._construct_controller(model, resource, version, controller,
                import_object(mixin_controller))

        return mount(resource, controller)

    def _construct_resource(self, archetype, resource, version, mixins):
        bases = tuple([resource] + list(mixins))
        return type(str(archetype.resource).capitalize(), bases, {
            'name': archetype.resource,
            'version': version,
            'requests': 'create delete get put query update',
            'schema': {
                'id': scheme.UUID(oncreate=True, operators='equal')
            },
        })

    def _construct_table(self, archetype):
        metadata = MetaData()
        parent = Table(archetype.config.model.__tablename__, metadata,
            Text(name='id', nullable=False, primary_key=True))

        tablename = self._prepare_tablename(archetype.config.prefix, archetype.id)
        table = Table(tablename, metadata,
            ForeignKey(name='id', column=parent.c.id, type_=TextType(),
                nullable=False, primary_key=True))

        return table

    def _prepare_tablename(self, prefix, id):
        tablename = id.lower().replace(':', '_')
        return prefix + '_' + re.sub(r'[^a-z_]', '', tablename).strip('_')
