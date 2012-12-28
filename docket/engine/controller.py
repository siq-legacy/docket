from mesh.exceptions import *
from mesh.standard import Controller
from spire.core import Unit
from spire.schema import SchemaDependency

class ProxyController(Unit, Controller):
    """A mesh controller for resources proxied by docket."""

    id = None
    client = None
    model = None
    schema = SchemaDependency('docket')

    def create(self, request, response, subject, data):
        extracted = self._extract_data('create', data)
        try:
            result = self._execute_request('create', data=extracted)
        except RequestError, exception:
            return response(exception.status, exception.content)

        entity = self.model(id=result.content['id'])
        for attr in ('name', 'designation', 'description'):
            if attr in data:
                setattr(entity, attr, data[attr])

        self.schema.session.add(entity)
        self.schema.session.commit()

        response({'id': entity.id})

    def query(self, request, response, subject, data):
        response({'resources': [], 'total': 0})

    def _extract_data(self, request, data):
        return self.client.extract(self.id, request, data)

    def _execute_request(self, request, subject=None, data=None):
        return self.client.execute(self.id, request, subject, data)
