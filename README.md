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

To run the tests, first install the dev requirements:

    pip install -r dev-requirements.txt

Then do:

    nosetests --nologcapture --with-pylons=test.ini

To run the tests with coverage, first install coverage (`pip install coverage`)
then do:

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.sweden --cover-inclusive --cover-erase --cover-tests


Theme
-----

To enable the theme:

1. Add `sweden_theme` to `ckan.plugins`

To modify the theme of the ckanext-sweden theme you'll need to:

1. Install [Node](http://nodejs.org/) (`apt-get install node`) and
   [Bower](http://bower.io/) (`npm install -g bower`)

2. Install the front end dependancies:
        cd ./ckanext/sweden/theme/ && npm i && bower update

3. Re-compile assets: `gulp` (`gulp watch` will regenerate them on the whenever
   a change happens.)

4. Once you've made your changes make sure you commit the changes in
   `./ckanext/theme/resources`
