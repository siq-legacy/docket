import re

from mesh.standard import Resource
from spire.core import Unit
from spire.runtime import current_runtime
from spire.schema import *
from spire.support.logs import LogHelper
from sqlalchemy import MetaData

from docket.engine.annotation import Annotator
from docket.models import Entity, Registration

log = LogHelper('docket')

class EntityRegistry(Unit):
    """The entity registry."""

    schema = SchemaDependency('docket')

    def __init__(self):
        self.proxies = {}
        self.annotator = Annotator(self.proxies)
        self.models = {}

    def bootstrap(self):
        session = self.schema.session
        for registration in session.query(Registration):
            model = self.models[registration.id] = self._construct_model(registration)
            self.annotator.process(registration, model)

        from docket.bundles import API
        API.attach(self.annotator.generate_mounts())

    def register(self, registration, changed=False):
        table = self._construct_table(registration)
        if changed or not self.schema.is_table_correct(table):
            current_runtime().reload()

    def unregister(self, registration):
        table = self._construct_table(registration)
        if self.schema.table_exists(table):
            self.schema.drop_table(table)
            current_runtime().reload()

    def _construct_model(self, registration):
        tablename = self._prepare_tablename(registration.id)
        meta = type('meta', (), {
            'polymorphic_identity': registration.id,
            'schema': self.schema.schema,
            'tablename': tablename,
        })

        attrs = {'meta': meta, 'entity_id': ForeignKey('entity.id', nullable=False,
            primary_key=True)}
        for name, attr in sorted(registration.cached_attributes.iteritems()):
            attrs[name] = attr.contribute_field()

        model = type(str(registration.title), (Entity,), attrs)
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
