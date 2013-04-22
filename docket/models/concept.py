from spire.schema import *

from docket import resources
from docket.models.archetype import Archetype
from docket.models.constituent import Constituent
from docket.resources.constituent import BaseConstituent
from docket.resources.entity import BaseEntity
from docket.resources.instance import BaseInstance

__all__ = ('Concept',)

schema = Schema('docket')

class Concept(Archetype):
    """A concept."""

    class meta:
        polymorphic_identity = 'docket:concept'
        schema = schema
        tablename = 'concept'

    class config:
        bundle = 'docket.CONCEPT_API'
        model = Constituent
        prefix = 'constituent'
        resources = [
            ((1, 0), (BaseConstituent[1], BaseInstance[1], BaseEntity[1]),
                'docket.controllers.constituent.BaseConstituentController'),
        ]

    archetype_id = ForeignKey(Archetype.entity_id, nullable=False, primary_key=True)
