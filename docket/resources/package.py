from mesh.standard import *
from scheme import *

from docket.resources.entity import BaseEntity

class Package(Resource, BaseEntity[1]):
    """An entity package."""

    name = 'package'
    version = 1

    class schema:
        id = Token(nonempty=True, oncreate=True, operators='equal')
        status = Enumeration('deployed undeployed', nullable=False, default='undeployed')
        package = Text()
