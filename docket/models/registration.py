from copy import deepcopy
import re

from spire.mesh.units import construct_mesh_client
from spire.schema import *
from spire.support.logs import LogHelper
from sqlalchemy.orm.collections import attribute_mapped_collection

__all__ = ('CachedAttribute', 'Registration')

ATTRIBUTE_FIELDS = {
    'boolean': Boolean,
    'date': Date,
    'datetime': DateTime,
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
    specification = Serialized(nullable=False)

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

    @classmethod
    def create(cls, session, cached_attributes=None, **params):
        registration = cls(**params)
        
        if cached_attributes:
            for name, attribute in cached_attributes.iteritems():
                registration.cached_attributes[name] = CachedAttribute(name=name, **attribute)

        session.add(registration)
        return registration

    def update(self, session, cached_attributes=None, **params):
        self.update_with_mapping(params)

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
