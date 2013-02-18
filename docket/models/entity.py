from mesh.standard import OperationError
from scheme import current_timestamp
from spire.schema import *
from spire.support.logs import LogHelper
from spire.util import uniqid

from docket.models.registration import Registration

log = LogHelper('docket')
schema = Schema('docket')

ContainerMembership = Table('container_membership', schema.metadata,
    ForeignKey(name='container_id', column='entity.id', nullable=False, primary_key=True),
    ForeignKey(name='member_id', column='entity.id', nullable=False, primary_key=True,
        ondelete='CASCADE'))

class Entity(Model):
    """An entity."""

    class meta:
        polymorphic_on = 'entity'
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

    containers = relationship('Entity', secondary=ContainerMembership,
        backref=backref('members'),
        primaryjoin=(id==ContainerMembership.c.member_id),
        secondaryjoin=(id==ContainerMembership.c.container_id),
        cascade='all', passive_deletes=True)

    is_container = False

    @classmethod
    def create(cls, session, containers=None, **attrs):
        subject = cls(**attrs)
        if not subject.id:
            subject.id = uniqid()

        if subject.created:
            subject.modified = subject.created
        else:
            subject.created = subject.modified = current_timestamp()

        session.add(subject)
        session.flush()

        if containers:
            subject.containers = cls._validate_containers(session, containers)

        return subject

    def describe_containers(self):
        description = []
        for container in self.containers:
            description.append({
                'id': container.id,
                'entity': container.entity,
                'name': container.name,
            })
        else:
            return description

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

    def update(self, session, containers=None, **attrs):
        self.update_with_mapping(attrs, ignore='id')
        self.modified = current_timestamp()

        if containers is not None:
            self.containers = self._validate_containers(session, containers)

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

    @classmethod
    def _validate_containers(cls, session, containers):
        entities = []
        for container in containers:
            try:
                entity = Entity.load(session, id=container['id'])
                if entity.is_container:
                    entities.append(entity)
                else:
                    raise OperationError(token='invalid-container')
            except NoResultFound:
                raise OperationError(token='unknown-container')
        else:
            return entities
