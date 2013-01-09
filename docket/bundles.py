from mesh.standard import Bundle, mount

from docket.resources import *

API = Bundle('docket',
    mount(Entity, 'docket.controllers.entity.EntityController'),
    mount(Package, 'docket.controllers.package.PackageController'),
    mount(Registration, 'docket.controllers.registration.RegistrationController'),
)
