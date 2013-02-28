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

    def create(self, request, response, subject, data):
        session = self.schema.session
        subject = self.model.create(session, data['subject'], data['intent'], data['target'])

        session.commit()
        response({'id': self._get_id_value(subject)})
