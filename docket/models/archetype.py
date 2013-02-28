from spire.mesh import Definition
from spire.schema import *
from spire.support.logs import LogHelper

from docket.models.entity import Entity
from docket.models.instance import Instance
from docket.resources.entity import BaseEntity
from docket.resources.instance import BaseInstance

log = LogHelper('docket')
schema = Schema('docket')

class Archetype(Entity):
    """An entity archetype."""

    class meta:
        polymorphic_identity = 'docket:archetype'
        schema = schema
        tablename = 'archetype'

    class config:
        bundle = 'docket.INSTANCE_API'
        model = Instance
        prefix = 'archetype'
        resources = [
            ((1, 0), (BaseInstance[1], BaseEntity[1]),
                'docket.controllers.instance.BaseInstanceController'),
        ]

    entity_id = ForeignKey(Entity.id, nullable=False, primary_key=True)
    resource = Token(segments=1, nullable=False, unique=True)
    attributes = Definition()
