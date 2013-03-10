from mesh.constants import RETURNING
from mesh.exceptions import *
from mesh.standard import Controller
from scheme import current_timestamp
from spire.core import Unit
from spire.mesh import field_included
from spire.mesh.controllers import FilterOperators
from spire.schema import NoResultFound, SchemaDependency
from sqlalchemy.sql import asc, desc

from docket.models import *

class Proxy(Unit):
    """An entity proxy.

    :param string id: The API id for this proxy, in the form `'resource:version'`.

    :param string identity: The resource identity for this proxy.

    :param list cached_attributes: A ``list`` containing the ``string`` names of
        the cached attributes for this proxy.

    :param client: The :class:`Client` for this proxy.

    :param dict fields: A ``dict`` mapping.
    """

    operators = FilterOperators()
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
        self.title = registration.title

    def __repr__(self):
        return 'Proxy(%r)' % self.id

    def acquire(self, id):
        try:
            return self.schema.session.query(self.model).get(id)
        except NoResultFound:
            return None

    def annotate_payload(self, payload):
        # this function is a hack
        if not payload:
            return
        if 'include' in payload:
            for key in ('associates', 'associations'):
                if key in payload['include']:
                    payload['include'].remove(key)

    def construct_resource(self, subject, resource, data):
        if field_included(data, 'associates'):
            resource['associates'] = subject.describe_associates()
        if field_included(data, 'associations'):
            resource['associations'] = subject.describe_associations()

        for attr, field in self.fields.iteritems():
            if attr not in resource and not field.deferred:
                resource[attr] = getattr(subject, attr)

    def create(self, data):
        session = self.schema.session
        self._acquire_registration_lock(session)

        attrs = dict((attr, value) for attr, value in data.iteritems() if attr in self.fields)
        subject = self.model.create(session, **attrs)
        session.flush()

        returning = list(self.cached_attributes)
        if not subject.name:
            returning.append('name')
        if self.created_is_proxied:
            returning.append('created')
        if self.modified_is_proxied:
            returning.append('modified')

        payload = self.extract_data('create', data)
        if returning:
            payload[RETURNING] = returning

        payload['id'] = subject.id
        result = self.execute_request('create', data=payload)

        attrs = result.content
        if self.created_is_proxied and not self.modified_is_proxied:
            attrs['modified'] = attrs['created']

        try:
            subject.update_with_mapping(attrs, ignore='id')
        except Exception:
            self._attempt_request('delete', subject.id)
            raise

        if not subject.name:
            subject.name = 'Unnamed %s' % self.title

        return subject

    def count(self):
        response = self.execute_request('query', data={'total': True})
        return response.content['total']

    def delete(self, subject, data=None):
        session = self.schema.session
        self._acquire_registration_lock(session)

        session.delete(subject)
        session.flush()

        try:
            self.execute_request('delete', subject.id, data)
        except GoneError:
            pass

    def extract_data(self, request, data):
        return self.client.extract(self.identity, request, data)

    def execute_request(self, request, subject=None, data=None, ignore_error=False):
        try:
            return self.client.execute(self.identity, request, subject, data)
        except ConnectionError:
            raise BadGatewayError()
        except RequestError:
            if not ignore_error:
                raise

    def get(self, subject, data=None):
        payload = self.extract_data('get', data)
        self.annotate_payload(payload)

        try:
            result = self.execute_request('get', subject.id, payload)
        except GoneError:
            resource = {'id': subject.id, 'defunct': True}
        else:
            resource = result.content

        self.construct_resource(subject, resource, data)
        return resource

    def iterate(self, limit, fields=None):
        total = self.count()
        offset = 0

        while offset < total:
            payload = {'offset': offset, 'limit': limit}
            if fields:
                payload['fields'] = fields

            response = self.execute_request('query', data=payload)
            for resource in response.content['resources']:
                yield resource
            else:
                offset += limit

    def load(self, identifiers, fields=None):
        single = False
        if isinstance(identifiers, basestring):
            identifiers = [identifiers]
            single = True

        payload = {'identifiers': identifiers}
        if fields:
            payload['fields'] = fields

        response = self.execute_request('load', data=payload)
        if single:
            return response.content[0]
        else:
            return response.content

    def query(self, data=None):
        # todo: needs to use data to request deferred fields via load
        attrs = self.fields.keys()
        data = data or {}
        query = self.schema.session.query(self.model)

        filters = data.get('query')
        if filters:
            query = self._construct_filters(query, filters)

        total = query.count()
        if data.get('total'):
            return {'total': total}

        if 'sort' in data:
            query = self._construct_sorting(query, data['sort'])
        if 'limit' in data:
            query = query.limit(data['limit'])
        if 'offset' in data:
            query = query.offset(data['offset'])

        subjects = list(query.all())
        if not subjects:
            return {'total': total, 'resources': []}

        payload = {'identifiers': [subject.id for subject in subjects]}
        if 'include' in data:
            payload['include'] = list(data['include'])

        self.annotate_payload(payload)
        result = self.execute_request('load', data=payload)

        resources = []
        for resource, subject in zip(result.content, subjects):
            if not resource:
                resource = {'id': subject.id, 'defunct': True}

            self.construct_resource(subject, resource, data)
            resources.append(resource)

        return {'total': total, 'resources': resources}

    def update(self, subject, data):
        if not data:
            return

        session = self.schema.session
        self._acquire_registration_lock(session)

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
        try:
            subject.update_with_mapping(attrs, ignore='id')
        except Exception:
            # schedule sync here
            pass

    def _acquire_registration_lock(self, session):
        registration = session.merge(self.registration, load=False)
        return registration.lock(session)

    def _attempt_request(self, request, subject=None, data=None):
        try:
            self.client.execute(self.identity, request, subject, data)
        except Exception:
            pass

    def _construct_filters(self, query, filters):
        model = self.model
        operators = self.operators

        for filter, value in filters.iteritems():
            if filter == 'associates__has':
                if value:
                    query = Association.query_associates(query, **value)
                continue
            elif filter == 'associations__has':
                if value:
                    query = Association.query_associations(query, **value)
                continue

            attr, operator = filter, 'equal'
            if '__' in filter:
                attr, operator = filter.rsplit('__', 1)

            column = getattr(model, attr)
            if not column:
                continue

            constructor = getattr(operators, operator + '_op')
            query = constructor(query, column, value)

        return query

    def _construct_sorting(self, query, sorting):
        model = self.model
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

class ProxyController(Unit, Controller):
    """A mesh controller for resources proxied by docket."""

    proxy = None
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
        try:
            response(self.proxy.get(subject, data))
        except RequestError, exception:
            response(exception.status, exception.content)

    def put(self, request, response, subject, data):
        if subject:
            self.update(request, response, subject, data)
        else:
            data['id'] = request.subject
            self.create(request, response, subject, data)

    def query(self, request, response, subject, data):
        try:
            response(self.proxy.query(data))
        except RequestError, exception:
            response(exception.status, exception.content)

    def update(self, request, response, subject, data):
        if not data:
            return response({'id': subject.id})

        try:
            self.proxy.update(subject, data)
        except RequestError, exception:
            return response(exception.status, exception.content)

        self.schema.session.commit()
        response({'id': subject.id})

