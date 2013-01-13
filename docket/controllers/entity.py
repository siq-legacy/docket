from spire.mesh import ModelController, field_included
from spire.schema import SchemaDependency

from docket.models import *
from docket.resources import Entity as EntityResource

class BaseEntityController(ModelController):
    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = self.model.create(session, **data)

        session.commit()
        response({'id': subject.id})

    def update(self, request, response, subject, data):
        session = self.schema.session
        if data:
            subject.update(session, **data)
            session.commit()

        response({'id': subject.id})

    def _annotate_resource(self, request, model, resource, data):
        if field_included(data, 'containers'):
            resource['containers'] = model.describe_containers()

class EntityController(BaseEntityController):
    resource = EntityResource
    version = (1, 0)

    model = Entity
    schema = SchemaDependency('docket')
    mapping = 'id entity name designation description created modified'

