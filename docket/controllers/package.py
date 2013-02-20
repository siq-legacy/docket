from mesh.standard import bind
from spire.core import Dependency
from spire.mesh import MeshDependency
from spire.schema import SchemaDependency

from docket.bindings import platoon

from docket.controllers.entity import BaseEntityController
from docket.engine.registry import EntityRegistry
from docket.models import *
from docket.resources.package import Package as PackageResource

ScheduledTask = bind(platoon, 'platoon/1.0/scheduledtask')

class PackageController(BaseEntityController):
    resource = PackageResource
    version = (1, 0)

    model = Package
    registry = Dependency(EntityRegistry)
    schema = SchemaDependency('docket')
    docket = MeshDependency('docket')
    mapping = 'id name designation description created modified package'

    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = self.model.create(session, **data)

        session.commit()

        if subject.status == 'deploying':
            task_params = {
                'task': 'deploy-package',
                'id': subject.id, }

            ScheduledTask.queue_http_task(
                'deploy-package',
                self.docket.prepare('docket/1.0/package', 'task',
                                    None, task_params) )

        response({'id': subject.id})
        return

    def task(self, request, response, subject, data):
        registry = self.registry
        session = self.schema.session

        if 'id' in data:
            try:
                subject = self.model.load(session, id=data['id'], lockmode='update')
            except NoResultFound:
                return

        task = data['task']
        if task == 'deploy-package':
            subject.deploy(registry, session)

        session.commit()
        return
