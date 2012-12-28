from mesh.standard import Bundle, mount

from docket.resources import *

API = Bundle('docket',
    mount(Registration, 'docket.controllers.registration.RegistrationController'),
)
