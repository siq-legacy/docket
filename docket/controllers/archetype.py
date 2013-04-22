from mesh.standard import bind
from spire.core import Dependency
from spire.mesh import MeshDependency
from spire.schema import SchemaDependency

from docket import resources
from docket.controllers.entity import BaseEntityController
from docket.engine.archetype_registry import ArchetypeRegistry
from docket.models import *

class BaseArchetypeController(BaseEntityController):
    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = self.model.create(session, **data)

        session.commit()
        response({'id': subject.id})

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
        changed = subject.update(session, **data)

        session.commit()
        response({'id': subject.id})

class ArchetypeController(BaseArchetypeController):
    resource = resources.Archetype
    version = (1, 0)

    model = Archetype
    registry = Dependency(ArchetypeRegistry)
    schema = SchemaDependency('docket')
    mapping = 'id name designation description created modified resource properties'
