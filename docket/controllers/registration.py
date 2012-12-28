from spire.core import Dependency
from spire.mesh import ModelController
from spire.schema import SchemaDependency

from docket.models import *
from docket.resources.registration import Registration as RegistrationResource
from docket.engine.registry import EntityRegistry

class RegistrationController(ModelController):
    resource = RegistrationResource
    version = (1, 0)

    model = Registration
    registry = Dependency(EntityRegistry)
    schema = SchemaDependency('docket')
    mapping = 'id name title url is_container specification'

    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = self.model.create(session, **data)

        session.commit()
        response({'id': subject.id})
        self.registry.register(subject)

    def delete(self, request, response, subject, data):
        session = self.schema.session
        session.delete(subject)

        session.commit()
        response({'id': subject.id})
        self.registry.unregister(subject)

    def update(self, request, response, subject, data):
        if not data:
            return response({'id': subject.id})

        session = self.schema.session
        subject.update(session, **data)

        session.commit()
        response({'id': subject.id})
        self.registry.register(subject)

    def _annotate_resource(self, request, model, resource, data):
        resource['cached_attributes'] = {}
        for name, attribute in model.cached_attributes.iteritems():
            resource['cached_attributes'][name] = attribute.extract_dict(
                exclude='id registration_id name')
