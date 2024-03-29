import scheme
from mesh.bundle import mount
from mesh.standard import Controller, Resource, bind
from mesh.standard.requests import add_schema_field
from spire.core import Unit
from spire.mesh import MeshDependency
from spire.runtime import current_runtime
from spire.schema import *
from spire.schema.construction import FieldConstructor
from spire.support.logs import LogHelper
from spire.util import import_object, safe_table_name
from sqlalchemy import MetaData

from docket import resources
from docket.bindings import platoon
from docket.models import *

log = LogHelper('docket')

PROTOTYPES = (Concept, DocumentType)

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

        constructor = FieldConstructor()
        if archetype.properties:
            for name, field in sorted(archetype.properties.structure.iteritems()):
                attrs[name] = constructor.construct(field)

        tablename = safe_table_name(archetype.id.replace(':', '_'), archetype.config.prefix)
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
        resource = type(str(archetype.resource).capitalize(), bases, {
            'name': archetype.resource,
            'version': version,
            'requests': 'create delete get put query update',
            'schema': {
                'id': scheme.UUID(oncreate=True, operators='equal')
            },
        })

        if archetype.properties:
            for name, field in archetype.properties.structure.iteritems():
                add_schema_field(resource, field)

        return resource

    def _construct_table(self, archetype):
        metadata = MetaData()
        parent = Table(archetype.config.model.__tablename__, metadata,
            Text(name='id', nullable=False, primary_key=True))

        tablename = safe_table_name(archetype.id.replace(':', '_'), archetype.config.prefix)
        table = Table(tablename, metadata,
            ForeignKey(name='id', column=parent.c.id, type_=TextType(),
                nullable=False, primary_key=True))

        return table

class StaticConstructor(object):
    def __init__(self, config, archetypes):
        self.archetypes = archetypes
        self.config = config

    def construct(self):
        bundle = import_object(self.config.bundle)
        for archetype in self.archetypes:
            bundle.attach([self._construct_mount(archetype)])
        return bundle

    def _construct_mount(self, archetype):
        resource = Resource
        controller = Controller

        for version, mixins, mixin_controller in self.config.resources:
            if resource.version != version[0]:
                resource = self._construct_resource(archetype, resource, version[0], mixins)

            controller = type('%sController' % resource.title, (controller,), {
                'resource': resource,
                'version': tuple(version),
            })

        return mount(resource, controller)

    def _construct_resource(self, archetype, resource, version, mixins):
        bases = tuple([resource] + list(mixins))
        resource = type(str(archetype['resource']).capitalize(), bases, {
            'name': archetype['resource'],
            'version': version,
            'requests': 'create delete get put query update',
            'schema': {
                'id': scheme.UUID(oncreate=True, operators='equal'),
            },
        })

        properties = archetype.get('properties')
        if properties:
            for name, field in scheme.Structure.reconstruct(properties).structure.iteritems():
                add_schema_field(resource, field)

        return resource
