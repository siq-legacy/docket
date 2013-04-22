from mesh.standard import Bundle, mount

from docket.resources import *

API = Bundle('docket',
    mount(Archetype, 'docket.controllers.archetype.ArchetypeController'),
    mount(Association, 'docket.controllers.association.AssociationController'),
    mount(DocumentType, 'docket.controllers.documenttype.DocumentTypeController'),
    mount(Entity, 'docket.controllers.entity.EntityController'),
    mount(Intent, 'docket.controllers.intent.IntentController'),
    mount(Package, 'docket.controllers.package.PackageController'),
    mount(Registration, 'docket.controllers.registration.RegistrationController'),
)

ENTITY_API = Bundle('docket.entity')
INSTANCE_API = Bundle('docket.instance')
CONCEPT_API = Bundle('docket.concept')
DOCUMENT_API = Bundle('docket.document')

BUNDLES = [API, CONCEPT_API, DOCUMENT_API, ENTITY_API, INSTANCE_API]
