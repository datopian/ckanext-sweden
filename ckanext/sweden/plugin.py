import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class SwedenPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IFacets)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

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

    def organization_facets(self, facets_dict, organization_type, package_type):
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
