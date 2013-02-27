from mesh.standard import bind
from spire.core import Dependency
from spire.mesh import MeshDependency
from spire.schema import *
from spire.support.logs import LogHelper

from docket.bindings import platoon
from docket.controllers.entity import BaseEntityController
from docket.engine.registry import EntityRegistry
from docket.models import *
from docket.resources.package import Package as PackageResource

log = LogHelper('docket')

ScheduledTask = bind(platoon, 'platoon/1.0/scheduledtask')

class PackageController(BaseEntityController):
    resource = PackageResource
    version = (1, 0)

    model = Package
    registry = Dependency(EntityRegistry)
    schema = SchemaDependency('docket')
    docket = MeshDependency('docket')
    mapping = 'id name designation description created modified package status'

    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = self.model.create(session, **data)

        log('info', 'create request for package %s', subject.id)

        try:
            session.commit()
        except IntegrityError:
            raise OperationError(token='duplicate-package')

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
        log('info', 'task request to %s', data['task'])

        registry = self.registry
        session = self.schema.session

        if 'id' in data:
            try:
                subject = self.model.load(session, id=data['id'], lockmode='update')
            except NoResultFound:
                return

        task = data['task']
        if task == 'deploy-package':
            subject.deploy(registry, session, method='create')
        elif task == 'update-package':
            subject.deploy(registry, session, method='update')

        if subject.status == 'invalid':
            session.rollback()
            subject.status = 'invalid'

        session.commit()

        return

    def update(self, request, response, subject, data):
        log('info', 'update request for package %s', subject.id)

        session = self.schema.session
        if not data:
            return response({'id': subject.id})

        subject.update(data)
        session.commit()

        if subject.status == 'deploying':
            task_params = {
                'task': 'update-package',
                'id': subject.id, }

            ScheduledTask.queue_http_task(
                'update-package',
                self.docket.prepare('docket/1.0/package', 'task',
                                    None, task_params) )

        response({'id': subject.id})

