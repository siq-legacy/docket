from mesh.standard import InvalidError, BadRequestError
from scheme import current_timestamp, Yaml
from spire.schema import *
from spire.support.logs import LogHelper

from docket.models.entity import Entity
from docket.models.registration import Registration

__all__ = ('Package',)

log = LogHelper('docket')
schema = Schema('docket')

class Package(Entity):
    """A package of entities."""

    class meta:
        polymorphic_identity = 'docket:package'
        schema = schema
        tablename = 'package'

    is_container = True

    entity_id = ForeignKey(Entity.id, nullable=False, primary_key=True)
    status = Enumeration('deployed undeployed deploying invalid', default='undeployed')
    package = Text()

    @classmethod
    def create(cls, session, **attrs):
        subject = super(Package, cls).create(session, **attrs)
        if subject.status == 'deployed':
            subject.status = 'deploying'
        return subject

    def update(self, data):
        current_entities = self._unserialize_entities(self.package)
        ce_dict = dict([(ce.get('id'), ce) for ce in current_entities])

        updated_entities = self._unserialize_entities(data.get('package', {}))
        for ue in updated_entities:
            ue_id = ue.get('id')
            if not ue_id:
                raise BadRequestError

            ce = ce_dict.get(ue_id)
            if ce:
                ce.update(ue)
            else:
                ce_dict[ue_id] = ue

        self.update_with_mapping(data)
        self.package = self._serialize_entities(ce_dict.values())

        self.modified = current_timestamp()
        if self.status == 'deployed':
            self.status = 'deploying'
        return

    def deploy(self, registry, session, method='create'):
        try:
            entities = self._unserialize_entities(self.package)
            for entity in entities:
                # remove type before passing entity down to proxy
                entity_type = entity.pop('entity', 'unknown')
                entity_id = entity.get('id', None)

                registration = session.query(Registration).get(entity_type)
                proxy = registration.get_canonical_proxy(registry)
                try:
                    if method == 'create' or not entity_id:
                        e = proxy.create(entity)
                        entity['id'] = e.id
                    elif method == 'update':
                        if entity_id:
                            e = proxy.acquire(entity_id)
                            e.update(entity)
                        else:
                            log('critical', '%s: no id for deployed entity %s:%s in package %s',
                                method, entity_type, str(entity), self.entity_id)
                    else:
                        raise NotImplementedError
                    # restore attributes before updating docket
                    entity['entity'] = entity_type
                except Exception, e:
                    log('critical', '%s: entity %s in package %s failed :',
                        method, entity_type, str(entity))
                    log('critical', '%s', str(e))
                    self.status = 'invalid'
                    break

            if not self.status == 'invalid':
                self.package = self._serialize_entities(entities)
                self.status = 'deployed'
        except Exception, e:
            log('exception', 'extraction of package %s failed : %s',
                self.entity_id, str(e))
            self.status = 'invalid'

        return

    def _serialize_entities(self, entities):
        return Yaml().serialize(entities)

    def _unserialize_entities(self, entities):
        return Yaml().unserialize(entities)
