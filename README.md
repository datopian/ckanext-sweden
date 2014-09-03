[![Build Status](https://travis-ci.org/okfn/ckanext-sweden.png)](https://travis-ci.org/okfn/ckanext-sweden) [![Coverage Status](https://coveralls.io/repos/okfn/ckanext-sweden/badge.png)](https://coveralls.io/r/okfn/ckanext-sweden)

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


Tests
-----

To run the tests:

    nosetests --nologcapture --with-pylons=test.ini

To run the tests with coverage, first install coverage (`pip install coverage`)
then do:

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.sweden --cover-inclusive --cover-erase --cover-tests
