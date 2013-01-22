from distutils.core import setup
from bake.packaging import *

setup(
    name='docket',
    version='0.0.1',
    packages=enumerate_packages('docket'),
    package_data={
        'docket.bindings': ['*.mesh'],
    }
)
