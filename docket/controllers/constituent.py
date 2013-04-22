from spire.schema import SchemaDependency

from docket.controllers.entity import BaseEntityController

class BaseConstituentController(BaseEntityController):
    schema = SchemaDependency('docket')
