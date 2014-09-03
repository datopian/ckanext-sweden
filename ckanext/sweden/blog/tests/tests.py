'''Functional tests for the blog plugin.'''
import webtest
import pylons.config as config

import ckan.config.middleware
import ckan.new_tests.factories as factories
import ckan.plugins.toolkit as toolkit

import ckanext.sweden.blog.tests.factories as custom_factories


def _get_test_app():
    '''Return a webtest.TestApp for CKAN, with legacy templates disabled.

    For functional tests that need to request CKAN pages or post to the API.
    Unit tests shouldn't need this.

    '''
    config['ckan.legacy_templates'] = False
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


def _load_plugin(plugin):
    '''Add the given plugin to the ckan.plugins config setting.

    This is for functional tests that need the plugin to be loaded.
    Unit tests shouldn't need this.

    If the given plugin is already in the ckan.plugins setting, it won't be
    added a second time.

    :param plugin: the plugin to add, e.g. ``"datastore"``
    :type plugin: string

    '''
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.add(plugin.strip())
    config['ckan.plugins'] = ' '.join(plugins)


def _initialise_blog_post_db_table():
    import ckan.model as model
    import ckanext.sweden.blog.model.post as post_model
    post_model.init_tables(model.meta.engine)


def _reset_blog_post_db_table():
    import ckan.model as model
    import ckanext.sweden.blog.model.post as post_model
    model.Session.query(post_model.Post).delete()


class FunctionalTestBaseClass(object):
    '''A base class for functional test classes to inherit from.

    This handles loading the sweden_blog plugin and resetting the CKAN config
    after your test class has run. It creates a webtest.TestApp at self.app for
    your class to use to make HTTP requests to the CKAN web UI or API.

    If you're overriding methods that this class provides, like setup_class()
    and teardown_class(), make sure to use super() to call this class's methods
    at the top of yours!

    '''
    @classmethod
    def setup_class(cls):
        # Make a copy of the Pylons config, so we can restore it in teardown.
        cls.original_config = config.copy()
        _load_plugin('sweden_blog')
        cls.app = _get_test_app()

    def setup(self):
        import ckan.model as model
        model.Session.close_all()
        model.repo.rebuild_db()
        _initialise_blog_post_db_table()
        _reset_blog_post_db_table()

    @classmethod
    def teardown_class(cls):
        # Restore the Pylons config to its original values, in case any tests
        # changed any config settings.
        config.clear()
        config.update(cls.original_config)


class TestBlog(FunctionalTestBaseClass):

    def _create_blog_post(self, title='Test blog post', content='Testing...',
                          extra_environ=None):
        '''Create a new blog post by submitting the form.

        We have to create blog posts this way whenever they're needed for tests
        because there's no API for creating them - the code that creates a
        post is in a controller method.

        '''
        if extra_environ is None:
            extra_environ = {}

        # Load the create post form, fill it in, and submit it.
        url = toolkit.url_for('blog_admin')
        response = self.app.get(url, extra_environ=extra_environ)
        form = response.forms[1]
        form['title'] = title
        form['content'] = content
        response = form.submit(extra_environ=extra_environ)
        return response

    def test_create_blog_post(self):
        '''Create a new blog post and visit its page.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        self._create_blog_post(extra_environ=extra_environ)

        # Load the page for the blog post we just created.
        url = toolkit.url_for('news_post', title='test-blog-post')
        response = self.app.get(url, extra_environ=extra_environ)
        assert response.status_int == 200
        soup = response.html
        assert soup('title')[0].text.startswith('Test blog post')
        assert 'Testing...' in soup.text

    def test_create_blog_post_with_no_title(self):
        '''Creating a blog post with no title should return an error.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        for title in ('', '   '):
            response = self._create_blog_post(title=title,
                                            content='This is my blog post',
                                            extra_environ=extra_environ)

            soup = response.html
            assert "You must enter a title" in soup.text
            assert "This is my blog post" in soup.text

    def test_edit_blog_post(self):
        '''Create a new blog post, edit it, and visit its page.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(extra_environ=extra_environ)

        # Edit the blog post we just created.
        url = toolkit.url_for('blog_admin_edit', title='test-blog-post')
        response = self.app.get(url, extra_environ=extra_environ)
        form = response.forms[1]
        form['title'] = 'Updated title'
        form['content'] = 'Updated content'
        response = form.submit(extra_environ=extra_environ)

        # Load the page for the blog post we just created.
        url = toolkit.url_for('news_post', title='test-blog-post')
        response = self.app.get(url, extra_environ=extra_environ)
        assert response.status_int == 200
        soup = response.html
        assert soup('title')[0].text.startswith('Updated title')
        assert 'Updated content' in soup.text

    def test_edit_blog_with_no_title(self):
        '''Updating a blog post with no title should return an error.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(extra_environ=extra_environ)

        for new_title in ('', '   '):

            # Edit the blog post we just created.
            url = toolkit.url_for('blog_admin_edit', title='test-blog-post')
            response = self.app.get(url, extra_environ=extra_environ)
            form = response.forms[1]
            form['title'] = new_title
            form['content'] = 'Updated content'
            response = form.submit(extra_environ=extra_environ)
            soup = response.html
            assert "You must enter a title" in soup.text
            assert "Updated content" in soup.text

            # Checl that the post has not been updated.
            url = toolkit.url_for('news_post', title='test-blog-post')
            response = self.app.get(url, extra_environ=extra_environ)
            assert response.status_int == 200
            soup = response.html
            assert soup('title')[0].text.startswith('Test blog post')
            assert 'Testing...' in soup.text

    def test_delete_blog_post(self):
        '''Create a new blog post then delete it.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        title = 'Test blog post'
        slug = 'test-blog-post'
        self._create_blog_post(title=title, extra_environ=extra_environ)

        # Load the blog admin index page and find the delete link for the post.
        url = toolkit.url_for('blog_admin_list')
        response = self.app.get(url, extra_environ=extra_environ)
        soup = response.html
        links = soup('a', href='/blog/admin/remove/' + slug)
        assert len(links) == 1
        link = links[0]
        url = link['href']

        # Click on the delete link.
        response = self.app.post(url, extra_environ=extra_environ)

        # Check that the blog post's page is no longer there.
        url = toolkit.url_for('news_post', title=slug)
        response = self.app.get(url, extra_environ=extra_environ, status=404)

        # Check the the blog post doesn't appear on the blog index page.
        url = toolkit.url_for('news')
        response = self.app.get(url)
        soup = response.html
        assert title not in soup.text

        # Check the the blog post doesn't appear on the blog admin index page.
        url = toolkit.url_for('blog_admin_list')
        response = self.app.get(url, extra_environ=extra_environ)
        soup = response.html
        assert title not in soup.text

    def test_front_page_when_no_posts_as_sysadmin(self):
        '''Test that the CKAN front page doesn't crash when there are no posts.

        '''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        self.app.get('/', extra_environ=extra_environ)

    def test_front_page_when_no_posts_and_not_logged_in(self):
        '''Test that the CKAN front page doesn't crash when there are no posts.

        '''
        self.app.get('/')

    def test_front_page_when_three_posts_as_sysadmin(self):
        '''The front page should show the latest post.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(title='Test post 1', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 2', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 3', extra_environ=extra_environ)

        response = self.app.get('/', extra_environ=extra_environ)
        soup = response.html
        assert 'Test post 3' in soup.text

    def test_front_page_when_three_posts_and_not_logged_in(self):
        '''The front page should show the latest post.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(title='Test post 1', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 2', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 3', extra_environ=extra_environ)

        response = self.app.get('/')
        soup = response.html
        assert 'Test post 3' in soup.text

    def test_index_page_when_no_posts_as_sysadmin(self):
        '''Test that the blog index page doesn't crash when there are no posts.

        '''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        url = toolkit.url_for('news')

        self.app.get(url, extra_environ=extra_environ)

    def test_index_page_when_no_posts_and_not_logged_in(self):
        '''Test that the blog index page doesn't crash when there are no posts.

        '''
        url = toolkit.url_for('news')

        self.app.get(url)

    def test_index_page_when_three_posts_as_sysadmin(self):
        '''The blog index page should show all the posts.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(title='Test post 1', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 2', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 3', extra_environ=extra_environ)
        url = toolkit.url_for('news')

        response = self.app.get(url, extra_environ=extra_environ)
        soup = response.html
        # TODO: We could test that the links to the blog pages are correct.
        # TODO: We could test that the posts appear in the right order.
        assert 'Test post 1' in soup.text
        assert 'Test post 2' in soup.text
        assert 'Test post 3' in soup.text

    def test_index_page_when_three_posts_and_not_logged_in(self):
        '''The blog index page should show all the posts.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(title='Test post 1', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 2', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 3', extra_environ=extra_environ)
        url = toolkit.url_for('news')

        response = self.app.get(url)
        soup = response.html
        # TODO: We could test that the links to the blog pages are correct.
        # TODO: We could test that the posts appear in the right order.
        assert 'Test post 1' in soup.text
        assert 'Test post 2' in soup.text
        assert 'Test post 3' in soup.text

    def test_feed_when_no_posts_as_sysadmin(self):
        '''Test that the RSS feed doesn't crash when there are no posts.'''
        url = toolkit.url_for('news_feed')
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        self.app.get(url, extra_environ=extra_environ)

    def test_feed_when_no_posts_and_not_logged_in(self):
        '''Test that the RSS feed doesn't crash when there are no posts.'''
        url = toolkit.url_for('news_feed')

        self.app.get(url)

    def test_feed_when_three_posts_as_sysadmin(self):
        '''The blog feed should show all the posts.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(title='Test post 1', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 2', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 3', extra_environ=extra_environ)
        url = toolkit.url_for('news_feed')

        response = self.app.get(url, extra_environ=extra_environ)
        # TODO: We could test that the links to the blog pages are correct.
        # TODO: We could test that the posts appear in the right order.
        assert 'Test post 1' in response.body
        assert 'Test post 2' in response.body
        assert 'Test post 3' in response.body

    def test_feed_when_three_posts_and_not_logged_in(self):
        '''The blog feed should show all the posts.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        self._create_blog_post(title='Test post 1', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 2', extra_environ=extra_environ)
        self._create_blog_post(title='Test post 3', extra_environ=extra_environ)
        url = toolkit.url_for('news_feed')

        response = self.app.get(url)
        # TODO: We could test that the links to the blog pages are correct.
        # TODO: We could test that the posts appear in the right order.
        assert 'Test post 1' in response.body
        assert 'Test post 2' in response.body
        assert 'Test post 3' in response.body

    # TODO: Test that visitors and non-sysadmins can't create/edit/delete posts.
    def test_visitor_cannot_create_post(self):
        '''Visitors (users who aren't logged-in) shouldn't be able to create
        blog posts.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        # Visitors should get a 302 when trying to load the 'create new blog
        # post' page.
        url = toolkit.url_for('blog_admin')
        response = self.app.get(url, status=302)

        # Load the page as a sysadmin, so we can get the form and submit it as
        # a visitor.
        response = self.app.get(url, extra_environ=extra_environ)

        # Visitors et a 302 (which is wrong!) when submitting the form.
        form = response.forms[1]
        form['title'] = 'Test blog post'
        form['content'] = 'Testing...'
        form.submit(status=302)

        # Test that the post didn't get created.
        url = toolkit.url_for('news')
        response = self.app.get(url)
        soup = response.html
        assert 'Test blog post' not in soup.text

    def test_user_cannot_create_post(self):
        '''Users who aren't sysadmins shouldn't be able to create blog posts.'''
        sysadmin = custom_factories.Sysadmin()
        user = factories.User()

        # Users should get a 302 when trying to load the 'create new blog
        # post' page.
        url = toolkit.url_for('blog_admin')
        response = self.app.get(
            url, extra_environ={'REMOTE_USER': str(user['name'])}, status=302)

        # Load the page as a sysadmin, so we can get the form and submit it as
        # a user.
        response = self.app.get(
            url, extra_environ={'REMOTE_USER': str(sysadmin['name'])})

        # Visitors et a 302 (which is wrong!) when submitting the form.
        form = response.forms[1]
        form['title'] = 'Test blog post'
        form['content'] = 'Testing...'
        form.submit(status=302,
                    extra_environ={'REMOTE_USER': str(user['name'])})

        # Test that the post didn't get created.
        url = toolkit.url_for('news')
        response = self.app.get(url)
        soup = response.html
        assert 'Test blog post' not in soup.text

    def test_visitor_cannot_edit_post(self):
        '''Visitors (users who aren't logged-in) shouldn't be able to edit
        blog posts.'''
        sysadmin = custom_factories.Sysadmin()
        self._create_blog_post(
            extra_environ={'REMOTE_USER': str(sysadmin['name'])})

        # Visitors get a 302 (which is wrong!) when trying to load the
        # edit blog post page.
        url = toolkit.url_for('blog_admin_edit', title='test-blog-post')
        response = self.app.get(url, status=302)

        # Load the page as a sysadmin so we can submit the form as a visitor.
        response = self.app.get(
            url, extra_environ={'REMOTE_USER': str(sysadmin['name'])})

        # Visitors get a 302 (which is wrong!) when trying to edit a blog post.
        form = response.forms[1]
        form['title'] = 'Updated title'
        form['content'] = 'Updated content'
        response = form.submit(status=302)

        # Test that the post hasn't been changed.
        url = toolkit.url_for('news_post', title='updated-title')
        response = self.app.get(url, status=404)
        url = toolkit.url_for('news_post', title='test-blog-post')
        response = self.app.get(url, status=200)

    def test_user_cannot_edit_post(self):
        '''Users who are not sysadmins shouldn't be able to edit blog posts.'''
        user = factories.User()
        sysadmin = custom_factories.Sysadmin()
        self._create_blog_post(
            extra_environ={'REMOTE_USER': str(sysadmin['name'])})

        # Users get a 302 (which is wrong!) when trying to load the
        # edit blog post page.
        url = toolkit.url_for(
            'blog_admin_edit', title='test-blog-post',
            extra_environ={'REMOTE_USER': str(user['name'])})
        response = self.app.get(url, status=302)

        # Load the page as a sysadmin so we can submit the form as a user.
        response = self.app.get(
            url, extra_environ={'REMOTE_USER': str(sysadmin['name'])})

        # Users get a 302 (which is wrong!) when trying to edit a blog post.
        form = response.forms[1]
        form['title'] = 'Updated title'
        form['content'] = 'Updated content'
        response = form.submit(status=302,
                               extra_environ={'REMOTE_USER': str(user['name'])})

        # Test that the post hasn't been changed.
        url = toolkit.url_for('news_post', title='updated-title')
        response = self.app.get(url, status=404)
        url = toolkit.url_for('news_post', title='test-blog-post')
        response = self.app.get(url, status=200)

    def test_visitor_cannot_delete_post(self):
        '''Visitors (users who aren't logged-in) shouldn't be able to delete
        posts.'''
        sysadmin = custom_factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}
        title = 'Test blog post'
        slug = 'test-blog-post'
        self._create_blog_post(title=title, extra_environ=extra_environ)

        url = toolkit.url_for('blog_admin_remove', title=slug)
        self.app.post(url, status=302)

        # Check that the blog post's page is still there.
        url = toolkit.url_for('news_post', title=slug)
        self.app.get(url, status=200)

    def test_user_cannot_delete_post(self):
        '''Users who aren't sysadmins shouldn't be able to delete posts.'''
        user = factories.User()
        sysadmin = custom_factories.Sysadmin()
        title = 'Test blog post'
        slug = 'test-blog-post'
        self._create_blog_post(
            title=title, extra_environ={'REMOTE_USER': str(sysadmin['name'])})

        url = toolkit.url_for('blog_admin_remove', title=slug)
        self.app.post(url, status=302,
                      extra_environ={'REMOTE_USER': str(user['name'])})

        # Check that the blog post's page is still there.
        url = toolkit.url_for('news_post', title=slug)
        self.app.get(url, status=200)
