import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultOrganizationForm

import ckanext.sweden.actions


class SwedenPlugin(plugins.SingletonPlugin, DefaultOrganizationForm):

    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IGroupForm, inherit=True)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    # IRoutes
    def before_map(self, _map):

        controller = 'ckanext.sweden.controllers:DCATController'

        _map.connect('dcat_organization', '/organization/{_id}/dcat.{_format}',
                     controller=controller, action='read_organization',
                     requirements={'_format': 'xml|rdf|n3|ttl'})
        _map.connect('dcat_validation',
                     '/organization/{_id}/dcat_validation.json',
                     controller=controller,
                     action='organization_dcat_validation')

        return _map

    # IPackageController

    def after_show(self, context, pkg_dict):
        '''
        Take the URI value for `theme` populated by dcat, transform it into a
        Eurovoc category label, and use it as the value for eurovoc category.
        '''
        theme_dict = next((i for i in pkg_dict.get('extras', [])
                           if i['key'] == 'theme'), {})
        theme = theme_dict.get('value', None)
        if theme is not None:
            try:
                theme_list = json.loads(theme)
            except ValueError:
                theme_list = [theme]
            pkg_dict['eurovoc_category'] = theme_list[0]
        return pkg_dict

    # IFacets

    def dataset_facets(self, facets_dict, package_type):
        facets_dict = self._update_facets(facets_dict)
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        facets_dict = self._update_facets(facets_dict)
        return facets_dict

    def organization_facets(self, facets_dict, organization_type,
                            package_type):
        facets_dict = self._update_facets(facets_dict)
        return facets_dict

    def _update_facets(self, facets_dict):
        '''Add `eurovoc_category_label` and change its position.'''

        new_position = 1  # new zero indexed position
        eurovoc_facet = {'eurovoc_category_label':
                         plugins.toolkit._('Eurovoc Categories')}

        if 'eurovoc_category_label' in facets_dict:
            del facets_dict['eurovoc_category_label']

        old_facets = facets_dict.copy()
        facets_dict.clear()
        for i, facet in enumerate(old_facets):
            if i == new_position:
                facets_dict.update(eurovoc_facet)
            facets_dict.update({facet: old_facets[facet]})

        return facets_dict

    # IGroupForm

    def is_fallback(self):
        return True

    def group_types(self):
        return ['organization']

    def form_to_db_schema(self):
        # Import core converters and validators
        _convert_to_extras = plugins.toolkit.get_converter('convert_to_extras')
        _url_validator = plugins.toolkit.get_validator('url_validator')
        _not_empty = plugins.toolkit.get_validator('not_empty')

        schema = super(SwedenPlugin, self).form_to_db_schema()

        schema.update({
            'url': [_not_empty, _strip_backslash, _url_validator,
                    _unique_org_url, _convert_to_extras, unicode],
        })

        return schema

    def db_to_form_schema(self):
        # Import core converters and validators
        _convert_from_extras = plugins.toolkit.get_converter(
            'convert_from_extras')
        _ignore_missing = plugins.toolkit.get_validator('ignore_missing')
        _not_empty = plugins.toolkit.get_validator('not_empty')

        schema = super(SwedenPlugin, self).form_to_db_schema()

        schema.update({
            'url': [_convert_from_extras, _ignore_missing],
            # TODO: this should be handled in core
            'num_followers': [_not_empty],
            'package_count': [_not_empty],
            'display_name': [_ignore_missing]
        })

        return schema

    # IActions

    def get_actions(self):
        action_functions = {
            'dcat_organization_list':
                ckanext.sweden.actions.dcat_organization_list,
            'dcat_validation':
                ckanext.sweden.actions.dcat_validation,
            'user_invite':
                ckanext.sweden.actions.user_invite,
        }
        return action_functions

    # IAuthFunctions

    def get_auth_functions(self):
        auth_functions = {
            'dcat_organization_list': dcat_auth,
            'dcat_validation': dcat_auth,
        }
        return auth_functions


# Auth functions

@toolkit.auth_allow_anonymous_access
def dcat_auth(context, data_dict):
    return {'success': True}


# Validators

def _unique_org_url(key, data, errors, context):

    value = data[key]

    model = context['model']

    q = model.Session.query(model.GroupExtra) \
             .filter(model.GroupExtra.key == 'url') \
             .filter(model.GroupExtra.value == value)

    org_id = data.get(('id',), '')
    org = model.Group.get(org_id)

    if org:
        q = q.filter(model.GroupExtra.group_id != org.id)

    count = q.count()

    if count:
        raise toolkit.Invalid(toolkit._(
            'There already is an organization with this URL: {0}'.format(
                data[key])))


def _strip_backslash(value, context):

    return value.rstrip('/')
