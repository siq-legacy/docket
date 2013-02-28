from bake import *
from scheme import Format, Text

from docket.bundles import API
from docket.engine.annotation import StaticAnnotator

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

        API.attach(annotator.generate_mounts())
        runtime.execute('mesh.javascript', path=self['path'], bundle=API)
