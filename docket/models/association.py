from mesh.standard import OperationError
from spire.schema import *

from docket.models.intent import Intent

__all__ = ('Association',)

schema = Schema('docket')

class Association(Model):
    """An entity association."""

    class meta:
        schema = schema
        tablename = 'association'

    subject_id = ForeignKey('entity.id', nullable=False, primary_key=True, ondelete='CASCADE')
    intent = ForeignKey('intent.id', nullable=False, primary_key=True, ondelete='CASCADE')
    target_id = ForeignKey('entity.id', nullable=False, primary_key=True)

    target = relationship('Entity', backref=backref('associates', lazy='dynamic'),
        primaryjoin=('Association.target_id==Entity.id'))

    @classmethod
    def create(cls, session, subject_id, intent, target_id):
        try:
            intent = Intent.load(session, id=intent)
        except NoResultFound:
            raise OperationError(token='invalid-intent')

        subject = cls(subject_id=subject_id, intent=intent.id, target_id=target_id)
        session.add(subject)
        return subject

    @classmethod
    def query_associates(cls, query, model, subject=None, intent=None, entity=None):
        query = query.join(model.associates)
        if subject:
            query = query.filter(cls.subject_id==subject)
        if intent:
            query = query.filter(cls.intent==intent)
        if entity:
            query = query.join(model, cls.subject_id==model.id,
                aliased=True).filter(model.entity==entity).reset_joinpoint()
        return query

    @classmethod
    def query_associations(cls, query, model, intent=None, target=None, entity=None):
        query = query.join(model.associations)
        if intent:
            query = query.filter(cls.intent==intent)
        if target:
            query = query.filter(cls.target_id==target)
        if entity:
            query = query.join(model, cls.target_id==model.id,
                aliased=True).filter(model.entity==entity).reset_joinpoint()
        return query
