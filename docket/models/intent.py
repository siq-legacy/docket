from spire.schema import *

from docket.models.entity import Entity

schema = Schema('docket')

class Intent(Entity):
    """An associational intent."""

    class meta:
        polymorphic_identity = 'docket:intent'
        schema = schema
        tablename = 'intent'

    id = ForeignKey(Entity.id, nullable=False, primary_key=True)
    exclusive = Boolean(default=False)

    uses = relationship('Association', backref='definition', lazy='dynamic',
        cascade='all', passive_deletes=True)
