from copy import deepcopy

from mesh.bundle import Bundle, mount, recursive_mount
from mesh.standard import *
from scheme import *

from docket.engine.controller import ProxyController
from docket.resources import Entity

def add_schema_field(resource, field, requests='create delete get put query update'):
    if isinstance(requests, basestring):
        requests = requests.split(' ')

    resource.schema[field.name] = field
    if 'create' in requests and not field.readonly:
        resource.requests['create'].schema.insert(field)
    if 'get' in requests:
        resource.requests['get'].responses[OK].schema.insert(field)
    if 'put' in resource.requests and 'put' in requests and not field.readonly:
        resource.requests['put'].schema.insert(field)
    if 'query' in requests:
        response = resource.requests['query'].responses[OK]
        response.schema.structure['resources'].item.insert(field)
    if 'update' in requests and not field.readonly:
        resource.requests['update'].schema.insert(field.clone(required=False))

class annotation(object):
    resource = Entity[1]
    version = (1, 0)

    @classmethod
    def construct(cls, registration, model):
        resource = Resource
        controller = ProxyController

        for version, description in cls._enumerate_versions(registration):
            resource_version = description['version'][0]
            if resource.version != resource_version:
                resource = cls._construct_resource(registration, resource, description)
            controller = cls._construct_controller(registration, resource, description,
                controller, model)

        return mount(resource, controller)

    @classmethod
    def _annotate_resource(cls, registration, resource):
        for name, field in cls.resource.filter_schema(exclude=True, annotational=True).iteritems():
            if name not in resource.schema:
                add_schema_field(resource, field)

    @classmethod
    def _construct_controller(cls, registration, resource, description, controller, model):
        return type('%sController' % resource.title, (controller,), {
            'client': registration.client,
            'id': description['id'],
            'model': model,
            'resource': resource,
            'version': tuple(description['version']),
        })

    @classmethod
    def _construct_resource(cls, registration, resource, description):
        resource = resource.reconstruct(deepcopy(description))
        cls._annotate_resource(registration, resource)
        return resource

    @classmethod
    def _enumerate_versions(cls, registration):
        name = registration.name
        for version, resources in sorted(registration.specification['versions'].iteritems()):
            yield version, resources[name]

class Annotator(object):
    """The resource annotator."""

    annotations = [annotation]

    def __init__(self):
        self.bundles = {}

    def generate_mounts(self):
        return [recursive_mount(bundle) for bundle in self.bundles.itervalues()]

    def process(self, registration, model):
        bundle_name = registration.specification['name']
        if bundle_name not in self.bundles:
            self.bundles[bundle_name] = {}
            for annotation in self.annotations:
                self.bundles[bundle_name][annotation.version] = Bundle(bundle_name)

        bundle = self.bundles[bundle_name]
        for annotation in self.annotations:
            mount = annotation.construct(registration, model)
            bundle[annotation.version].attach([mount])
