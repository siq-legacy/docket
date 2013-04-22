from spire.mesh import ModelController
from spire.schema import NoResultFound, SchemaDependency

from docket.models import *
from docket.resources.form import Form as FormResource

class FormController(ModelController):
    resource = FormResource
    version = (1, 0)

    model = Form
    schema = SchemaDependency('docket')
    mapping = 'id title schema layout'
