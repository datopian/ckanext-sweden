import logging
from webhelpers.markdown import markdown
from ckan import model
from ckan.lib.base import (h, c, BaseController, request, response, abort)
from ckan.lib.helpers import flash_notice
import ckan.plugins.toolkit as toolkit
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


def _validate_blog_post(data_dict, original_title=None):

    title = data_dict.get('title').strip()
    if not title:
        raise ValidationError(toolkit._("You must enter a title"))

    from ckanext.sweden.blog.model.post import Post
    q = model.Session.query(Post).filter_by(title=title)
    if original_title:
        q = q.filter(Post.url != original_title)
    if q.all():
        raise ValidationError(toolkit._(
            "There's already a post with that title"))

    content = data_dict.get('content', '')

    return title, content


class BlogController(BaseController):

    def index(self):
        from ckanext.sweden.blog.model.post import Post

        c.posts = model.Session.query(Post).\
            filter(Post.visible == True).order_by('created desc')

        return toolkit.render('blog/index.html')

    def admin_index(self):
        # Redirect to /news if not authorized:
        try:
            context = {'user': c.user}
            toolkit.check_access('blog_admin', context)
        except toolkit.NotAuthorized:
            h.redirect_to('/news')

        from ckanext.sweden.blog.model.post import Post

        c.posts = model.Session.query(Post).\
            filter(Post.visible == True).order_by('created desc')

        return toolkit.render('blog/admin_list.html')

    def admin_remove(self, title):
        # Redirect to /news if not authorized:
        try:
            context = {'user': c.user}
            toolkit.check_access('blog_admin', context)
        except toolkit.NotAuthorized:
            h.redirect_to('/news')

        if request.method != "POST":
            abort(405)

        try:
            from ckanext.sweden.blog.model.post import Post
            post = model.Session.query(Post).filter(Post.url == title).one()
        except NoResultFound:
            abort(404)

        model.Session.delete(post)
        model.Session.commit()
        flash_notice(toolkit._("The blog post has been removed!"))

        h.redirect_to(
            controller='ckanext.sweden.blog.controllers.blog:BlogController',
            action='admin_index')

    def read(self, title):
        try:
            from ckanext.sweden.blog.model.post import Post
            c.post = model.Session.query(Post).\
                filter(Post.url == title).\
                filter(Post.visible == True).\
                one()
        except NoResultFound:
            abort(404)

        c.content_markdown = markdown(c.post.content)
        c.post_author = (model.User.get(c.post.user_id)
                         or model.Session.query(model.User).filter_by(
                             id=c.post.user_id).first())

        return toolkit.render('blog/post.html')

    def admin(self):
        # Redirect to /news if not authorized:
        try:
            context = {'user': c.user}
            toolkit.check_access('blog_admin', context)
        except toolkit.NotAuthorized:
            h.redirect_to('/news')

        c.title = ''
        c.content = ''
        if request.method == 'POST':

            try:
                title, content = _validate_blog_post(request.POST)
            except ValidationError as err:
                return toolkit.render('blog/admin.html',
                                      extra_vars={'data_dict': request.POST,
                                                  'error': err.args})

            # We assume nothing will go wrong here, since the data has been
            # validated.
            from ckanext.sweden.blog.model.post import Post
            newPost = Post(title, content, c.userobj.id)
            model.Session.add(newPost)
            model.Session.commit()
            flash_notice(toolkit._("Your blog post has been saved!"))

            controller = 'ckanext.sweden.blog.controllers.blog:BlogController'
            h.redirect_to(controller=controller, action='admin_index')

        return toolkit.render('blog/admin.html',
                              extra_vars={'data_dict': {}, 'error': ''})

    def admin_edit(self, title):
        data_dict = dict(request.POST)

        # Redirect to /news if not authorized:
        try:
            context = {'user': c.user}
            toolkit.check_access('blog_admin', context)
        except toolkit.NotAuthorized:
            h.redirect_to('/news')

        try:
            from ckanext.sweden.blog.model.post import Post
            c.post = model.Session.query(Post).\
                filter(Post.url == title).\
                filter(Post.visible == True).\
                one()
            if 'title' not in data_dict:
                data_dict['title'] = c.post.title
            if 'content' not in data_dict:
                data_dict['content'] = c.post.content
        except NoResultFound:
            abort(404)

        if request.method == 'POST':

            try:
                title, content = _validate_blog_post(
                    request.POST, original_title=request.urlvars.get('title'))
            except ValidationError as err:
                return toolkit.render(
                    'blog/admin_edit.html',
                    extra_vars={'data_dict': data_dict, 'error': err.args})

            c.post.title = title
            c.post.content = content
            model.Session.commit()

            flash_notice(toolkit._("Your blog post has been updated!"))

            controller = 'ckanext.sweden.blog.controllers.blog:BlogController'
            h.redirect_to(controller=controller, action='admin_index')

        return toolkit.render(
            'blog/admin_edit.html',
            extra_vars={'data_dict': data_dict, 'errors': ''})

    def feed(self):
        from ckanext.sweden.blog.model.post import Post

        c.posts = model.Session.query(Post).\
            filter(Post.visible == True).order_by('created desc')

        response.headers['Content-Type'] = 'application/rss+xml'
        response.charset = 'utf-8'

        return toolkit.render('blog/rss.html')
