import factory

import ckan.model
import ckan.new_tests.helpers as helpers


def _generate_email(user):
    '''Return an email address for the given User factory stub object.'''

    return '{0}@ckan.org'.format(user.name).lower()


class Sysadmin(factory.Factory):
    '''A factory class for creating sysadmin users.'''

    FACTORY_FOR = ckan.model.User

    fullname = 'Mr. Test Sysadmin'
    password = 'pass'
    about = 'Just another test sysadmin.'

    name = factory.Sequence(lambda n: 'test_sysadmin_{n}'.format(n=n))

    email = factory.LazyAttribute(_generate_email)
    sysadmin = True

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError(".build() isn't supported in CKAN")

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        user = target_class(**dict(kwargs, sysadmin=True))
        ckan.model.Session.add(user)
        ckan.model.Session.commit()
        ckan.model.Session.remove()

        # We want to return a user dict not a model object, so call user_show
        # to get one. We pass the user's name in the context because we want
        # the API key and other sensitive data to be returned in the user
        # dict.
        user_dict = helpers.call_action('user_show', id=user.id,
                                        context={'user': user.name})
        return user_dict
