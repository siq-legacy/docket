from copy import deepcopy

from mesh.bundle import Bundle, mount, recursive_mount
from mesh.standard import *
from scheme import *

from docket.engine.controller import ProxyController
from docket.resources import Entity

def add_schema_field(resource, field):
    resource.schema[field.name] = field
    resource.requests['get'].responses[OK].schema.insert(field)

    response = resource.requests['query'].responses[OK]
    response.schema.structure['resources'].item.insert(field)

    if not field.readonly:
        if field.oncreate is not False:
            resource.requests['create'].schema.insert(field)
        if field.onupdate is not False:
            resource.requests['update'].schema.insert(field.clone(required=False))
        if 'put' in resource.requests and field.onput is not False:
            resource.requests['put'].schema.insert(field)

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
        for name, field in cls.resource.filter_schema(True, annotational=True).iteritems():
            if name not in resource.schema:
                add_schema_field(resource, field)

    @classmethod
    def _construct_controller(cls, registration, resource, description, controller, model):
        cached_attributes = []
        for name, attribute in registration.cached_attributes.iteritems():
            if name in resource.schema:
                cached_attributes.append(name)

        fields = {}
        for name, field in cls.resource.filter_schema(True, annotational=True).iteritems():
            fields[name] = resource.schema[name]

        return type('%sController' % resource.title, (controller,), {
            'cached_attributes': cached_attributes,
            'client': registration.client,
            'created_is_proxied': (not fields['created'].annotational),
            'fields': fields,
            'id': description['id'],
            'model': model,
            'modified_is_proxied': (not fields['modified'].annotational),
            'registration': registration,
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
