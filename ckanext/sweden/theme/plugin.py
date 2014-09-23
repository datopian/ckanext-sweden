import ckan.plugins as p

class ThemePlugin(p.SingletonPlugin):
    """This extension adds the ckanext-theme to ckan

    This extension implements two interfaces

      - ``IConfigurer`` allows to modify the configuration
      - ``IConfigurable`` get the configuration
    """
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)

    def update_config(self, config):
        ''' Set up template, public and fanstatic directories
        '''
        config['ckan.site_logo'] = '/images/logo.png'
        config['ckan.favicon'] = '/images/favicon.ico'

        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')
        p.toolkit.add_resource('resources', 'theme')
