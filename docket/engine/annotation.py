from copy import deepcopy

from mesh.bundle import Bundle, mount, recursive_mount
from mesh.standard import *
from mesh.standard.requests import add_schema_field
from scheme import *

from docket.engine.controller import Proxy, ProxyController
from docket.resources import Entity

__all__ = ('Annotation', 'Annotator')

class Annotation(object):
    resource = Entity[1]
    version = (1, 0)

    @classmethod
    def construct(cls, registration, model):
        resource = Resource
        controller = ProxyController

        proxies = {}
        for version, description in cls._enumerate_versions(registration):
            resource_version = description['version'][0]
            if resource.version != resource_version:
                resource = cls._construct_resource(registration, resource, description)
            proxy = cls._construct_proxy(registration, resource, description, model)
            proxies[proxy.id] = proxy
            controller = cls._construct_controller(resource, description, controller, proxy)

        return proxies, mount(resource, controller)

    @classmethod
    def _annotate_resource(cls, registration, resource):
        for name, field in cls.resource.schema.iteritems():
            if name not in resource.schema and field.annotational:
                add_schema_field(resource, field)

    @classmethod
    def _construct_controller(cls, resource, description, controller, proxy):
        return type('%sController' % resource.title, (controller,), {
            'proxy': proxy,
            'resource': resource,
            'version': tuple(description['version']),
        })

    @classmethod
    def _construct_proxy(cls, registration, resource, description, model):
        cached_attributes = []
        for name, attribute in registration.cached_attributes.iteritems():
            if name in resource.schema:
                cached_attributes.append(name)

        fields = {}
        for name, field in cls.resource.schema.iteritems():
            if field.annotational:
                fields[name] = resource.schema[name]

        created_is_proxied = (not fields['created'].annotational)
        modified_is_proxied = (not fields['modified'].annotational)

        id = '%s:%d.%d' % (registration.id, description['version'][0], description['version'][1])
        return Proxy(id, description['id'], cached_attributes, registration.client, fields,
            model, registration, created_is_proxied, modified_is_proxied)

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

    annotations = [Annotation]

    def __init__(self, proxies=None):
        self.bundles = {}
        self.proxies = proxies

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
            proxies, mount = annotation.construct(registration, model)
            if self.proxies is not None:
                self.proxies.update(proxies)
            bundle[annotation.version].attach([mount])
