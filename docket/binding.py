class RegistrationSupport(object):
    mixin = 'Registration'

    @staticmethod
    def prepare_specifications(description, name):
        specifications = {}
        for version, resources in description['versions'].iteritems():
            if name in resources:
                specifications['%d.%d' % version] = resources[name]
        return specifications
