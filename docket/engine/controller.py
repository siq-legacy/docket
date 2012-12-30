from mesh.constants import RETURNING
from mesh.exceptions import *
from mesh.standard import Controller
from scheme import current_timestamp
from spire.core import Unit
from spire.mesh.controllers import FilterOperators
from spire.schema import NoResultFound, SchemaDependency
from sqlalchemy.sql import asc, desc

class ProxyController(Unit, Controller):
    """A mesh controller for resources proxied by docket."""

    id = None
    cached_attributes = None
    client = None
    created_is_proxied = False
    fields = None
    model = None
    modified_is_proxied = False
    registration = None

    operators = FilterOperators()
    schema = SchemaDependency('docket')

    def acquire(self, subject):
        try:
            return self.schema.session.query(self.model).get(subject)
        except NoResultFound:
            return None

    def create(self, request, response, subject, data):
        returning = self.cached_attributes
        if self.created_is_proxied:
            returning = ['created'] + returning

        payload = self._extract_data('create', data)
        if returning:
            payload[RETURNING] = returning

        try:
            result = self._execute_request('create', data=payload)
        except RequestError, exception:
            return response(exception.status, exception.content)

        subject = self.model(**result.content)
        if subject.created:
            subject.modified = subject.created
        else:
            subject.created = subject.modified = current_timestamp()

        for attr, field in self.fields.iteritems():
            if attr in data:
                setattr(subject, attr, data[attr])

        self.schema.session.add(subject)
        self.schema.session.commit()
        response({'id': subject.id})

    def delete(self, request, response, subject, data):
        try:
            result = self._execute_request('delete', subject.id, data)
        except RequestError, exception:
            return response(exception.status, exception.content)

        self.schema.session.delete(subject)
        self.schema.session.commit()
        response({'id': subject.id})

    def get(self, request, response, subject, data):
        try:
            result = self._execute_request('get', subject.id)
        except RequestError, exception:
            return response(exception.status, exception.content)

        resource = result.content
        for attr, field in self.fields.iteritems():
            if attr not in resource:
                resource[attr] = getattr(subject, attr)

        response(resource)

    def put(self, request, response, subject, data):
        if subject:
            self.update(request, response, subject, data)
        else:
            data['id'] = request.subject
            self.create(request, response, subject, data)

    def query(self, request, response, subject, data):
        attrs = self.fields.keys()
        data = data or {}
        query = self.schema.session.query(self.model)

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
        try:
            payload = {'identifiers': [subject.id for subject in subjects]}
            result = self._execute_request('load', data=payload)
        except RequestError, exception:
            return response(exception.status, exception.content)

        resources = result.content
        for resource, subject in zip(resources, subjects):
            for attr in attrs:
                if attr not in resource:
                    resource[attr] = getattr(subject, attr)

        response({'total': total, 'resources': resources})

    def update(self, request, response, subject, data):
        if not data:
            return response({'id': subject.id})

        returning = self.cached_attributes
        if self.modified_is_proxied:
            returning = ['modified'] + returning

        payload = self._extract_data('update', data)
        if returning:
            payload[RETURNING] = returning

        try:
            result = self._execute_request('update', subject.id, payload)
        except RequestError, exception:
            return response(exception.status, exception.content)

        subject.update_with_mapping(result.content)
        if not self.modified_is_proxied:
            subject.modified = current_timestamp()

        for attr, field in self.fields.iteritems():
            if attr in data:
                setattr(subject, attr, data[attr])

        self.schema.session.commit()
        response({'id': subject.id})

    def _construct_filters(self, query, filters):
        model, operators = self.model, self.operators
        for filter, value in filters.iteritems():
            attr, operator = filter, 'equal'
            if '__' in filter:
                attr, operator = filter.rsplit('__', 1)

            constructor = getattr(operators, operator + '_op')
            query = constructor(query, getattr(model, attr), value)

        return query

    def _construct_sorting(self, query, sorting):
        columns = []
        for attr in sorting:
            direction = asc
            if attr[-1] == '+':
                attr = attr[:-1]
            elif attr[-1] == '-':
                attr = attr[:-1]
                direction = desc

            column = getattr(self.model, attr)
            columns.append(direction(column))

        return query.order_by(*columns)

    def _extract_data(self, request, data):
        return self.client.extract(self.id, request, data)

    def _execute_request(self, request, subject=None, data=None):
        return self.client.execute(self.id, request, subject, data)
