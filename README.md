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


DCAT Harvesting
---------------

To enable, activate your CKAN virtual environment and then:

1. Install Redis:

    sudo apt-get install redis-server

2. Install `ckanext-harvest`:

        git clone https://github.com/ckan/ckanext-harvest
        cd ckanext-harvest
        git checkout stable
        pip install -r pip-requirements.txt
        python setup.py develop

3. Install `ckanext-dcat`:

        git clone https://github.com/ckan/ckanext-dcat
        cd ckanext-dcat
        pip install -r requirements.txt
        # tmp
        pip install lxml
        python setup.py develop

5. Add `harvest`  and `dcat_rdf_harvester` to `ckan.plugins`.

6. Restart CKAN.

You should see the harvest pages at `/harvest` and `Generic DCAT RDF Harvester`
listed as a type on `/harvest/new`.

### Configuration options

The following configuration options can be used with regards to the validation
of remote DCAT documents:

* `ckanext.sweden.harvest.use_validation` (default: `True`): Whether to use validation at all
* `ckanext.sweden.harvest.validation_service` (default: `http://validator.dcat-editor.com/service`): The
   URL of the validation service to use. The harvester will POST the contents of the remote DCAT file
   to this endpoint.
* `ckanext.sweden.harvest.stop_on_validation_errors` (default `False`): Whether to stop the datasets import
   if validation errors were found.


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


Eurovoc categories
------------------

Eurovoc categories can be added to the dataset schema by installing [ckanext-eurovoc](https://github.com/ckan/ckanext-eurovoc).

    pip install ckanext-eurovoc

Then edit the configuration file by adding `eurovoc` to `ckan.plugins`.


Tests
-----

To run the tests, first install the dev requirements (and Redis, see above):

    pip install -r dev-requirements.txt

Then do:

    nosetests --nologcapture --ckan --with-pylons=test.ini

To run the tests with coverage, first install coverage (`pip install coverage`)
then do:

    nosetests --nologcapture --ckan --with-pylons=test.ini --with-coverage --cover-package=ckanext.sweden --cover-inclusive --cover-erase --cover-tests



