from mesh.standard import Bundle, mount

from docket.resources import *

API = Bundle('docket',
    mount(Entity, 'docket.controllers.entity.EntityController'),
    mount(Registration, 'docket.controllers.registration.RegistrationController'),
)
