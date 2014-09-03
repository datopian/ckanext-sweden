ckanext-sweden
==============

CKAN extension for Öppnadata.se, the Swedish data management platform.


Blog Plugin
-----------

To enable:

1. Add `sweden_blog` to `ckan.plugins`.

2. Run the paster command to initialize the blog's database tables:

        paster --plugin=ckan sweden_blog_init -c /etc/ckan/default/development.ini

3. Restart CKAN.
