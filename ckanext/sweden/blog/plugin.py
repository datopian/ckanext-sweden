from logging import getLogger

import ckan.plugins as p
import ckan.lib.base as base
from webhelpers.markdown import markdown
from webhelpers.text import truncate
from ckan import model
from ckan.model import Session
from sqlalchemy.orm.exc import NoResultFound

from ckanext.sweden.blog.authorize import blog_admin

log = getLogger(__name__)

def latest_post():
    '''Return the most recent blog post.

    Returns None if there are no blog posts.

    :rtype: ckanext.sweden.blog.model.post.Post or None

    '''
    try:
      from ckanext.sweden.blog.model.post import Post
      post = Session.query(Post).\
          filter(Post.visible == True).\
          order_by('created desc').\
          first()
    except NoResultFound, e:
      return None

    if post is None:
        return None

    post.content_markdown = markdown(unicode(truncate(post.content, length=320, indicator='...', whole_word=True)))
    post.post_author = model.User.get(post.user_id) or Session.query(model.User).filter_by(id=post.user_id).first()

    return post

class BlogPlugin(p.SingletonPlugin):
    """This extension adds blogging functionality to ckan

    This extension implements four interfaces

      - ``IConfigurer`` allows to modify the configuration
      - ``IConfigurable`` get the configuration
      - ``IAuthFunctions`` to add custom authorization
      - ``IRoutes`` to add custom routes
    """
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=False)
    p.implements(p.IRoutes, inherit=True)

    def get_auth_functions(self):
        return {
            'blog_admin' : blog_admin
        }

    def get_helpers(self):
        return {'latest_post': latest_post}

    def before_map(self, map):
        blog_controller = 'ckanext.sweden.blog.controllers.blog:BlogController'
        map.connect('news', '/news', controller=blog_controller, action='index')
        map.connect('news_feed', '/news.rss', controller=blog_controller, action='feed')
        map.connect('blog_admin', '/blog/admin/create', controller=blog_controller, action='admin')
        map.connect('blog_admin_list', '/blog/admin', controller=blog_controller, action='admin_index')
        map.connect('blog_admin_remove', '/blog/admin/remove/{title}', controller=blog_controller, action='admin_remove')
        map.connect('blog_admin_edit', '/blog/admin/edit/{title}', controller=blog_controller, action='admin_edit')
        map.connect('news_post', '/news/{title}', controller=blog_controller, action='read')
        return map

    def after_map(self, map):
        return map


    def update_config(self, config):
        ''' Set up template directory
        '''
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_resource('fanstatic', 'blog')
