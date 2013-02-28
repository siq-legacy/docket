from mesh.standard import Bundle, mount

from docket.resources import *

__all__ = ('API', 'CONCEPT_API', 'DOCUMENT_API', 'INSTANCE_API')

API = Bundle('docket',
    #mount(Archetype, 'docket.controllers.archetype.ArchetypeController'),
    mount(Association, 'docket.controllers.association.AssociationController'),
    mount(Entity, 'docket.controllers.entity.EntityController'),
    mount(Intent, 'docket.controllers.intent.IntentController'),
    mount(Package, 'docket.controllers.package.PackageController'),
    mount(Registration, 'docket.controllers.registration.RegistrationController'),
)

INSTANCE_API = Bundle('docket.instance')
CONCEPT_API = Bundle('docket.concept')
DOCUMENT_API = Bundle('docket.document')
