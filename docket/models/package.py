from mesh.standard import InvalidError
from scheme import Yaml
from spire.schema import *
from spire.support.logs import LogHelper

from docket.models.entity import Entity
from docket.models.registration import Registration

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
    status = Enumeration('deployed undeployed deploying', default='undeployed')
    package = Text()

    @classmethod
    def create(cls, session, containers=None, **attrs):
        subject = super(Package, cls).create(session, containers, **attrs)
        if subject.status == 'deployed':
            subject.status = 'deploying'
        return subject

    def deploy(self, registry, session):
        try:
            entities = Yaml().unserialize(self.package)
            for entity in entities:
                entity_type = entity.pop('entity')
                entity.setdefault('containers', None)
                registration = session.query(Registration).get(entity_type)
                proxy = registration.get_canonical_proxy(registry)

                try:
                    proxy.create(entity)
                except InvalidError, e:
                    log('critical', 'creation of entity %s:%s in package %s failed : %s',
                        entity_type, str(entity), self.entity_id, str(e))
                    continue
        except Exception, e:
            log('exception', 'extraction of package %s failed : %s',
                self.entity_id, str(e))
            return

        self.status = 'deployed'
        return

