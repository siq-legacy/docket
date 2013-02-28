from mesh.standard import OperationError
from scheme import current_timestamp
from spire.schema import *
from spire.support.logs import LogHelper
from spire.util import uniqid

from docket.models.registration import Registration

log = LogHelper('docket')
schema = Schema('docket')

class Entity(Model):
    """An entity."""

    class meta:
        polymorphic_on = 'entity'
        polymorphic_identity = 'docket:entity'
        schema = schema
        tablename = 'entity'

    id = Text(nullable=False, primary_key=True)
    entity = Token(nullable=False, index=True)
    name = Text(nullable=False, index=True)
    designation = Text(index=True)
    description = Text()
    created = DateTime(timezone=True, nullable=False)
    modified = DateTime(timezone=True, nullable=False)
    defunct = Boolean(nullable=False, default=False)

    associations = relationship('Association', backref='subject', lazy='dynamic',
        primaryjoin='Entity.id==Association.subject_id',
        cascade='all', passive_deletes=True)

    is_container = False

    def __repr__(self):
        return '%s(id=%r, name=%r)' % (type(self).__name__, self.id, self.name)

    @classmethod
    def create(cls, session, **attrs):
        subject = cls(**attrs)
        if not subject.id:
            subject.id = uniqid()

        if subject.created:
            subject.modified = subject.created
        else:
            subject.created = subject.modified = current_timestamp()

        session.add(subject)
        return subject

    def describe_associates(self):
        associates = []
        for associate in self.associates.options(joinedload('subject')):
            subject = associate.subject
            associates.append({
                'subject': subject.id,
                'intent': associate.intent,
                'entity': subject.entity,
                'name': subject.name,
            })
        return associates

    def describe_associations(self):
        associations = []
        for association in self.associations.options(joinedload('target')):
            target = association.target
            associations.append({
                'intent': association.intent,
                'target': target.id,
                'entity': target.entity,
                'name': target.name,
            })
        return associations

    def get_registration(self, session):
        return session.query(Registration).get(self.entity)

    def synchronize(self, registry, session):
        """Synchronize this entity with its contributing component."""

        registration = self.get_registration(session)
        proxy = registration.get_canonical_proxy(registry)

        resource = proxy.load(self.id, proxy.cached_attributes)
        if resource:
            self._synchronize_entity(proxy, resource)
        else:
            self.defunct = True

    @classmethod
    def synchronize_entities(cls, registry, session):
        """Synchronizes all docket entities with their respective components."""

        registrations = list(session.query(Registration))
        for registration in registrations:
            registration.lock(session, True)
            try:
                self._synchronize_entities(session, registration)
            except Exception:
                session.rollback()
            else:
                session.commit()

    def update(self, session, **attrs):
        self.update_with_mapping(attrs, ignore='id')
        self.modified = current_timestamp()

    @classmethod
    def _synchronize_entities(cls, registry, session, registration):
        query = session.query(cls)
        identifiers = set()

        proxy = registration.get_canonical_proxy(registry)
        fields = ['id'] + proxy.cached_attributes

        for resource in proxy.iterate(2000):
            entity = query.get(resource['id'])
            if entity:
                entity._synchronize_entity(proxy, resource)
                identifiers.add(entity.id)
            else:
                entity = cls.create(session, **resource)
                identifiers.add(entity.id)

        for entity in query.all():
            if entity.id not in identifiers:
                entity.defunct = True

    def _synchronize_entity(self, proxy, data):
        for attr in proxy.cached_attributes:
            if attr in data:
                setattr(self, attr, data[attr])

        # todo: handle entity attrs
