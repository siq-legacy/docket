from spire.mesh import ModelController, field_included
from spire.schema import NoResultFound, SchemaDependency

from docket.models import *
from docket.resources import Association as AssociationResource

class AssociationController(ModelController):
    resource = AssociationResource
    version = (1, 0)

    model = Association
    schema = SchemaDependency('docket')
    mapping = ('id', ('subject', 'subject_id'), 'intent', ('target', 'target_id'))
