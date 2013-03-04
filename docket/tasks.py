from bake import *
from scheme import Format, Text
from spire.util import import_object

from docket.bundles import ENTITY_API
from docket.engine.annotation import StaticAnnotator
from docket.engine.archetype_registry import StaticConstructor

class GenerateJavascriptBindings(Task):
    name = 'docket.javascript'
    parameters = {
        'config': Text(description='path to registration config', required=True),
        'path': Path(description='path to target directory', required=True),
        'specifications': Path(description='path to specifications directory', required=True),
    }

    def run(self, runtime):
        annotator = StaticAnnotator()
        for registration in Format.read(self['config']):
            candidate = self['specifications'] / registration['id'].replace(':', '_')
            if candidate.exists():
                registration['specification'] = eval(candidate.bytes())
                annotator.process(registration)

        ENTITY_API.attach(annotator.generate_mounts())
        runtime.execute('mesh.javascript', path=self['path'], bundle=ENTITY_API)

class GenerateArchetypeBindings(Task):
    name = 'docket.javascript.archetypes'
    parameters = {
        'config': Text(description='path to archetypes config', required=True),
        'path': Path(description='path to target directory', required=True),
    }

    def run(self, runtime):
        path = self['path']
        for registration in Format.read(self['config']):
            implementation = import_object(registration['implementation'])
            constructor = StaticConstructor(implementation.config, registration['archetypes'])
            runtime.execute('mesh.javascript', path=path, bundle=constructor.construct())
