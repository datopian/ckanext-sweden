import ckan.plugins as p
from ckan import model

def _get_datasets(sort):
  context = {'model': model, 'session': model.Session,
             'user': p.toolkit.c.user, 'for_view': True,
             'auth_user_obj': p.toolkit.c.userobj}
  data_dict = {'rows': 3, 'start': 0, 'sort': sort}
  query = p.toolkit.get_action('package_search')(context, data_dict)
  if (query['results']):
    return query['results']
  return False

def get_most_viewed_datasets():
  return _get_datasets('views desc')

def get_recently_updated_datasets():
    return _get_datasets('metadata_modified desc')

def get_top_groups():
  return

def get_recent_blog_posts():
    from ckanext.sweden.blog.model.post import Post
    posts = model.Session.query(Post).\
      filter(Post.visible == True).order_by('created desc').limit(3)
    return posts

class ThemePlugin(p.SingletonPlugin):
    """This extension adds the ckanext-theme to ckan

    This extension implements two interfaces

      - ``IConfigurer`` allows to modify the configuration
      - ``IConfigurable`` get the configuration
    """
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=False)

    def get_helpers(self):
        return {
          'get_most_viewed_datasets': get_most_viewed_datasets,
          'get_recently_updated_datasets': get_recently_updated_datasets,
          'get_top_groups': get_top_groups,
          'get_recent_blog_posts': get_recent_blog_posts
        }

    def update_config(self, config):
        ''' Set up template, public and fanstatic directories
        '''
        config['ckan.site_logo'] = '/images/logo.png'
        config['ckan.favicon'] = '/images/favicon.ico'

        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')
        p.toolkit.add_resource('resources', 'theme')
