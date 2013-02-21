from copy import deepcopy
from functools import partial
import re

from spire.mesh.units import construct_mesh_client
from spire.schema import *
from spire.support.logs import LogHelper
from sqlalchemy.orm import deferred
from sqlalchemy.orm.collections import attribute_mapped_collection

__all__ = ('CachedAttribute', 'Registration')

ATTRIBUTE_FIELDS = {
    'boolean': Boolean,
    'date': Date,
    'datetime': partial(DateTime, timezone=True),
    'decimal': Decimal,
    'float': Float,
    'integer': Integer,
    'text': Text,
    'time': Time,
}

log = LogHelper('docket')
schema = Schema('docket')

class Registration(Model):
    """An entity registration."""

    class meta:
        schema = schema
        tablename = 'registration'

    id = Token(segments=2, nullable=False, primary_key=True)
    name = Token(segments=1, nullable=False)
    title = Text(nullable=False)
    url = Text(nullable=False)
    is_container = Boolean(nullable=False, default=False)
    specification = deferred(Serialized(nullable=False))
    canonical_version = Text()
    change_event = Text()
    standard_entities = Json()

    cached_attributes = relationship('CachedAttribute', backref='registration',
        collection_class=attribute_mapped_collection('name'),
        cascade='all,delete-orphan', passive_deletes=True)

    _cached_clients = {}

    @property
    def client(self):
        try:
            return self._cached_clients[self.id]
        except KeyError:
            client = construct_mesh_client(self.url, deepcopy(self.specification))
            self._cached_clients[self.id] = client
            return client

    def annotate(self, model):
        model.is_container = self.is_container

    def as_resource(self):
        cached_attributes = {}
        for name, attribute in self.cached_attributes.iteritems():
            cached_attributes[name] = attribute.extract_dict(
                exclude='id registration_id name')

        return self.extract_dict(cached_attributes=cached_attributes)

    @classmethod
    def create(cls, session, cached_attributes=None, **params):
        registration = cls(**params)
        if cached_attributes:
            for name, attribute in cached_attributes.iteritems():
                registration.cached_attributes[name] = CachedAttribute(name=name, **attribute)

        session.add(registration)
        return registration

    def create_standard_entities(self, session, model):
        entities = self.standard_entities
        if not entities:
            return []

        identifiers = []
        for entity in entities:
            identifiers.append(entity['id'])
            try:
                subject = model.load(session, id=entity['id'])
            except NoResultFound:
                subject = model.create(session, **entity)
            else:
                subject.update_with_mapping(entity, ignore='id')
        else:
            return identifiers

    def get_canonical_proxy(self, registry):
        return registry.get_proxy(self.id, self.get_canonical_version())

    def get_canonical_version(self):
        if self.canonical_version:
            return self.canonical_version

        try:
            return self._cached_canonical_version
        except AttributeError:
            self._cached_canonical_version = self._identify_latest_api_version()
            return self._cached_canonical_version

    def lock(self, session, exclusive=False):
        session.refresh(self, lockmode=('update' if exclusive else 'read'))
        return self

    def update(self, session, cached_attributes=None, **params):
        changed = False
        for attr, value in params.iteritems():
            if getattr(self, attr) != value:
                setattr(self, attr, value)
                changed = True

        if cached_attributes is not None:
            collection = self.cached_attributes
            for name, attribute in cached_attributes.iteritems():
                if name in collection:
                    collection[name].update_with_mapping(attribute)
                else:
                    collection[name] = CachedAttribute(name=name, **attribute)
            for name in collection.keys():
                if name not in cached_attributes:
                    del collection[name]

        return changed

    def _identify_latest_api_version(self):
        versions = sorted(map(int, v.split('.')) for v in self.specification['versions'].keys())
        return '%d.%d' % (tuple(versions[-1]))

class CachedAttribute(Model):
    """An entity attribute."""

    class meta:
        constraints = [UniqueConstraint('registration_id', 'name')]
        schema = schema
        tablename = 'cached_attribute'

    id = Identifier()
    registration_id = ForeignKey('registration.id', nullable=False, ondelete='CASCADE')
    name = Text(nullable=False)
    type = Token(nullable=False)

    def contribute_field(self):
        field = ATTRIBUTE_FIELDS[self.type]
        return field(name=self.name)
