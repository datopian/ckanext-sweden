import json

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class SwedenPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)

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
