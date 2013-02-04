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
        session = self.schema.session
        attrs = dict((attr, value) for attr, value in data.iteritems() if attr in self.fields)

        subject = self.model.create(session, **attrs)
        session.flush()

        returning = self.cached_attributes
        if self.created_is_proxied:
            returning = ['created'] + returning

        payload = self.extract_data('create', data)
        if returning:
            payload[RETURNING] = returning

        payload['id'] = subject.id
        result = self.execute_request('create', data=payload)

        attrs = result.content
        if self.created_is_proxied:
            attrs['modified'] = attrs['created']

        attrs.pop('id', None)
        try:
            subject.update_with_mapping(attrs)
        except Exception:
            self._attempt_request('delete', subject.id)
            raise
        else:
            return subject

    def delete(self, subject, data=None):
        session = self.schema.session
        session.delete(subject)

        session.flush()
        try:
            self.execute_request('delete', subject.id, data)
        except GoneError:
            pass

    def extract_data(self, request, data):
        return self.client.extract(self.identity, request, data)

    def execute_request(self, request, subject=None, data=None):
        try:
            return self.client.execute(self.identity, request, subject, data)
        except ConnectionError:
            raise BadGatewayError()

    def load(self, identifiers):
        single = False
        if isinstance(identifiers, basestring):
            identifiers = [identifiers]
            single = True

        payload = {'identifiers': identifiers}
        results = self.execute_request('load', data=payload)

        if single:
            return results[0]
        else:
            return results

    def update(self, subject, data):
        if not data:
            return

        session = self.schema.session
        attrs = dict((attr, value) for attr, value in data.iteritems() if attr in self.fields)

        subject.update(session, **attrs)
        session.flush()

        returning = self.cached_attributes
        if self.modified_is_proxied:
            returning = ['modified'] + returning

        payload = self.extract_data('update', data)
        if not payload:
            return
        if returning:
            payload[RETURNING] = returning

        try:
            result = self.execute_request('update', subject.id, payload)
        except GoneError:
            subject.defunct = True
            return

        attrs = result.content
        attrs.pop('id', None)

        try:
            subject.update_with_mapping(attrs)
        except Exception:
            # schedule sync here
            pass

    def _attempt_request(self, request, subject=None, data=None):
        try:
            self.client.execute(self.identity, request, subject, data)
        except Exception:
            pass

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
        except GoneError:
            resource = {'id': subject.id, 'defunct': True}
        except RequestError, exception:
            return response(exception.status, exception.content)
        else:
            resource = result.content

        for attr in self.fields.iterkeys():
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

        payload = {'identifiers': [subject.id for subject in subjects]}
        try:
            result = self.proxy.execute_request('load', data=payload)
        except RequestError, exception:
            return response(exception.status, exception.content)

        resources = []
        for resource, subject in zip(result.content, subjects):
            if not resource:
                resource = {'id': subject.id, 'defunct': True}
            for attr in attrs:
                if attr not in resource:
                    resource[attr] = getattr(subject, attr)
            self._annotate_resource(request, subject, resource, data)
            resources.append(resource)

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
