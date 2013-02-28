from mesh.standard import OperationError
from spire.core import Dependency
from spire.mesh import ModelController, field_included
from spire.schema import NoResultFound, SchemaDependency

from docket.engine.registry import EntityRegistry
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

    def _annotate_filter(self, query, filter, value):
        if filter == 'associations__has':
            if value:
                query = Association.query_associations(query, self.model, **value)
            return query
        elif filter == 'associates__has':
            if value:
                query = Association.query_associates(query, self.model, **value)
            return query

    def _annotate_resource(self, request, model, resource, data):
        if field_included(data, 'associations'):
            resource['associations'] = model.describe_associations()
        if field_included(data, 'associates'):
            resource['associates'] = model.describe_associates()

class EntityController(BaseEntityController):
    resource = EntityResource
    version = (1, 0)

    model = Entity
    registry = Dependency(EntityRegistry)
    schema = SchemaDependency('docket')
    mapping = 'id entity name designation description created modified'

    def task(self, request, response, subject, data):
        registry = self.registry
        session = self.schema.session

        task = data['task']
        if task == 'synchronize-entities':
            self.model.synchronize_entities(registry, session)
        elif task == 'synchronize-entity':
            for identifier in data['ids']:
                try:
                    subject = self.model.load(session, id=data['id'], lockmode='update')
                except NoResultFound:
                    continue
                else:
                    subject.synchronize(registry, session)
                    session.commit()
        elif task == 'synchronize-changed-entity':
            event = data.get('event')
            if not event:
                return

            try:
                subject = self.model.load(session, id=event['id'], lockmode='update')
            except NoResultFound:
                return
            else:
                subject.synchronize(registry, session)
                session.commit()
