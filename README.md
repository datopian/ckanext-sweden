ckanext-sweden
==============

CKAN extension for Öppnadata.se, the Swedish data management platform.


Blog Plugin
-----------

To enable, activate your CKAN virtual environment and then:

1. Add `sweden_blog` to `ckan.plugins`.

2. Install the blog plugin's requirements:

        pip install -r ckanext/sweden/blog/requirements.txt

3. Run the paster command to initialize the blog's database tables:

        paster --plugin=ckan sweden_blog_init -c /etc/ckan/default/development.ini

4. Restart CKAN.
