from mesh.standard import *
from scheme import *

from docket.resources.entity import BaseEntity

class Package(Resource, BaseEntity[1]):
    """An entity package."""

    name = 'package'
    version = 1

    class schema:
        id = Token(nonempty=True, oncreate=True, operators='equal')
        status = Enumeration('deployed undeployed deploying invalid', nullable=False, default='undeployed')
        package = Text()

    class task:
        endpoint = ('TASK', 'package')
        schema = Structure(
            structure={
                'deploy-package': {
                    'id': Token(nonempty=True),
                },
                'update-package': {
                    'id': Token(nonempty=True),
                },
            },
            nonempty=True,
            polymorphic_on=Enumeration([
                'deploy-package', 'update-package'],
                name='task', nonempty=True))
        responses = {
            OK: Response(),
            INVALID: Response(Errors),
        }


