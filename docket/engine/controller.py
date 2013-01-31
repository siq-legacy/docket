from mesh.constants import RETURNING
from mesh.exceptions import *
from mesh.standard import Controller
from scheme import current_timestamp
from spire.core import Unit
from spire.mesh import field_included
from spire.mesh.controllers import FilterOperators
from spire.schema import NoResultFound, SchemaDependency
from sqlalchemy.sql import asc, desc

class Proxy(Unit):
    """An entity proxy."""

    schema = SchemaDependency('docket')

    def __init__(self, id, identity, cached_attributes, client, fields, model, registration,
            created_is_proxied=False, modified_is_proxied=False):

        self.cached_attributes = cached_attributes
        self.client = client
        self.created_is_proxied = created_is_proxied
        self.fields = fields
        self.id = id
        self.identity = identity
        self.model = model
        self.modified_is_proxied = modified_is_proxied
        self.registration = registration

    def __repr__(self):
        return 'Proxy(%r)' % self.id

    def acquire(self, id):
        try:
            return self.schema.session.query(self.model).get(id)
        except NoResultFound:
            return None

    def create(self, data):
        # TODO: change this so that we flush the create to docket first, then attempt the request down
        returning = self.cached_attributes
        if self.created_is_proxied:
            returning = ['created'] + returning

        payload = self.extract_data('create', data)
        if returning:
            payload[RETURNING] = returning

        result = self.execute_request('create', data=payload)
        try:
            return self._create_entity(result.content, data)
        except Exception:
            self._attempt_request('delete', result.content['id'])
            raise

    def delete(self, subject, data=None):
        self.schema.session.delete(subject)
        self.schema.session.flush()
        self.execute_request('delete', subject.id, data)

    def extract_data(self, request, data):
        return self.client.extract(self.identity, request, data)

    def execute_request(self, request, subject=None, data=None):
        try:
            return self.client.execute(self.identity, request, subject, data)
        except ConnectionError:
            raise BadGatewayError()

    def update(self, subject, data):
        if not data:
            return

        returning = self.cached_attributes
        if self.modified_is_proxied:
            returning = ['modified'] + returning

        payload = self.extract_data('update', data)
        if returning:
            payload[RETURNING] = returning

        result = self.execute_request('update', subject.id, payload)
        params = result.content

        for attr, field in self.fields.iteritems():
            if attr in data:
                params[attr] = data[attr]

        session = self.schema.session
        subject.update(session, **params)

    def _attempt_request(self, request, subject=None, data=None):
        try:
            self.client.execute(self.identity, request, subject, data)
        except Exception:
            pass

    def _create_entity(self, parameters, data):
        for attr, field in self.fields.iteritems():
            if attr in data:
                parameters[attr] = data[attr]

        session = self.schema.session
        return self.model.create(session, **parameters)

    def _update_entity(self, subject, parameters, data):
        for attr, field in self.fields.iteritems():
            if attr in data:
                parameters[attr] = data[attr]

        session = self.schema.session
        subject.update(session, **parameters)

class ProxyController(Unit, Controller):
    """A mesh controller for resources proxied by docket."""

    proxy = None

    operators = FilterOperators()
    schema = SchemaDependency('docket')

    def acquire(self, subject):
        return self.proxy.acquire(subject)

    def create(self, request, response, subject, data):
        try:
            subject = self.proxy.create(data)
        except RequestError, exception:
            return response(exception.status, exception.content)

        self.schema.session.commit()
        response({'id': subject.id})

    def delete(self, request, response, subject, data):
        try:
            self.proxy.delete(subject, data)
        except RequestError, exception:
            return response(exception.status, exception.content)

        self.schema.session.commit()
        response({'id': subject.id})

    def get(self, request, response, subject, data):
        payload = self.proxy.extract_data('get', data)
        try:
            result = self.proxy.execute_request('get', subject.id, payload)
        except RequestError, exception:
            return response(exception.status, exception.content)

        resource = result.content
        for attr, field in self.fields.iteritems():
            if attr not in resource:
                resource[attr] = getattr(subject, attr)

        self._annotate_resource(request, subject, resource, data)
        response(resource)

    def put(self, request, response, subject, data):
        if subject:
            self.update(request, response, subject, data)
        else:
            data['id'] = request.subject
            self.create(request, response, subject, data)

    def query(self, request, response, subject, data):
        attrs = self.proxy.fields.keys()
        data = data or {}
        query = self.schema.session.query(self.proxy.model)

        filters = data.get('query')
        if filters:
            query = self._construct_filters(query, filters)

        total = query.count()
        if data.get('total'):
            return response({'total': total})

        if 'sort' in data:
            query = self._construct_sorting(query, data['sort'])
        if 'limit' in data:
            query = query.limit(data['limit'])
        if 'offset' in data:
            query = query.offset(data['offset'])

        subjects = list(query.all())
        if not subjects:
            return response({'total': total, 'resources': []})

        subjects = list(query.all())
        try:
            payload = {'identifiers': [subject.id for subject in subjects]}
            result = self.proxy.execute_request('load', data=payload)
        except RequestError, exception:
            return response(exception.status, exception.content)

        resources = result.content
        for resource, subject in zip(resources, subjects):
            for attr in attrs:
                if attr not in resource:
                    resource[attr] = getattr(subject, attr)
            self._annotate_resource(request, subject, resource, data)

        response({'total': total, 'resources': resources})

    def update(self, request, response, subject, data):
        if not data:
            return response({'id': subject.id})

        try:
            self.proxy.update(subject, data)
        except RequestError, exception:
            return response(exception.status, exception.content)

        self.schema.session.commit()
        response({'id': subject.id})

    def _annotate_resource(self, request, model, resource, data):
        if field_included(data, 'containers'):
            resource['containers'] = model.describe_containers()

    def _construct_filters(self, query, filters):
        model, operators = self.proxy.model, self.operators
        for filter, value in filters.iteritems():
            attr, operator = filter, 'equal'
            if '__' in filter:
                attr, operator = filter.rsplit('__', 1)

            constructor = getattr(operators, operator + '_op')
            query = constructor(query, getattr(model, attr), value)

        return query

    def _construct_sorting(self, query, sorting):
        model = self.proxy.model
        columns = []
        for attr in sorting:
            direction = asc
            if attr[-1] == '+':
                attr = attr[:-1]
            elif attr[-1] == '-':
                attr = attr[:-1]
                direction = desc

            column = getattr(model, attr)
            columns.append(direction(column))

        return query.order_by(*columns)
