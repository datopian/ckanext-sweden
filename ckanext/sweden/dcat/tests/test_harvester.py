import nose
import httpretty

import ckan.new_tests.helpers as h

import ckanext.harvest.model as harvest_model
from ckanext.harvest import queue

from ckanext.sweden.dcat.harvester import RDFDCATHarvester


eq_ = nose.tools.eq_


# This horrible monkey patch is needed because httpretty does not play well
# with redis, so we need to disable it straight after the mocked call is used.
# See https://github.com/gabrielfalcao/HTTPretty/issues/113

# Start monkey-patch

original_get_content = RDFDCATHarvester._get_content


def _patched_get_content(self, url, harvest_job, page=1):

    httpretty.enable()

    value = original_get_content(self, url, harvest_job, page)

    httpretty.disable()

    return value

RDFDCATHarvester._get_content = _patched_get_content

# End monkey-patch


class TestDCATHarvestUnit(object):

    def test_get_guid_uri(self):

        dataset = {
            'name': 'test-dataset',
            'extras': [
                {'key': 'uri', 'value': 'http://dataset/uri'},
                {'key': 'dcat_identifier', 'value': 'dataset_dcat_id'},
            ]
        }

        guid = RDFDCATHarvester()._get_guid(dataset)

        eq_(guid, 'http://dataset/uri')

    def test_get_guid_dcat_identifier(self):

        dataset = {
            'name': 'test-dataset',
            'extras': [
                {'key': 'dcat_identifier', 'value': 'dataset_dcat_id'},
            ]
        }

        guid = RDFDCATHarvester()._get_guid(dataset)

        eq_(guid, 'dataset_dcat_id')

    def test_get_guid_source_url_name(self):

        dataset = {
            'name': 'test-dataset',
            'extras': [
            ]
        }

        guid = RDFDCATHarvester()._get_guid(dataset, 'http://source_url')

        eq_(guid, 'http://source_url/test-dataset')

        guid = RDFDCATHarvester()._get_guid(dataset, 'http://source_url/')

        eq_(guid, 'http://source_url/test-dataset')

    def test_get_guid_name(self):

        dataset = {
            'name': 'test-dataset',
            'extras': [
            ]
        }

        guid = RDFDCATHarvester()._get_guid(dataset)

        eq_(guid, 'test-dataset')

    def test_get_guid_none(self):

        dataset = {
            'extras': [
            ]
        }

        guid = RDFDCATHarvester()._get_guid(dataset)

        eq_(guid, None)


class TestDCATHarvestFunctional(object):

    @classmethod
    def setup_class(cls):

        raise nose.SkipTest

        cls.gather_consumer = queue.get_consumer('ckan.harvest.gather.test',
                                                 'harvest_job_id')
        cls.fetch_consumer = queue.get_consumer('ckan.harvest.fetch.test',
                                                'harvest_object_id')

        cls.mock_url = 'http://some.dcat.file.rdf'

        # Minimal remote RDF file
        cls.remote_file = '''<?xml version="1.0" encoding="utf-8" ?>
        <rdf:RDF
         xmlns:dct="http://purl.org/dc/terms/"
         xmlns:dcat="http://www.w3.org/ns/dcat#"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <dcat:Catalog rdf:about="https://data.some.org/catalog">
          <dcat:dataset>
            <dcat:Dataset rdf:about="https://data.some.org/catalog/datasets/1">
              <dct:title>Example dataset 1</dct:title>
            </dcat:Dataset>
          </dcat:dataset>
          <dcat:dataset>
            <dcat:Dataset rdf:about="https://data.some.org/catalog/datasets/2">
              <dct:title>Example dataset 2</dct:title>
            </dcat:Dataset>
          </dcat:dataset>
        </dcat:Catalog>
        </rdf:RDF>
        '''

    def setup(self):

        harvest_model.setup()

        self.gather_consumer.queue_purge(queue='ckan.harvest.gather.test')
        self.fetch_consumer.queue_purge(queue='ckan.harvest.fetch.test')

    def teardown(cls):
        h.reset_db()

    def _create_harvest_source(self):

        source_dict = {
            'title': 'Test RDF DCAT Source',
            'name': 'test-rdf-dcat-source',
            'url': self.mock_url,
            'source_type': 'dcat_rdf',
        }

        harvest_source = h.call_action('harvest_source_create',
                                       {}, **source_dict)

        eq_(harvest_source['source_type'], 'dcat_rdf')

        return harvest_source

    def _create_harvest_job(self, harvest_source_id):

        harvest_job = h.call_action('harvest_job_create',
                                    {}, source_id=harvest_source_id)

        return harvest_job

    def _run_jobs(self, harvest_source_id=None):
        try:
            h.call_action('harvest_jobs_run',
                          {}, source_id=harvest_source_id)
        except Exception, e:
            if (str(e) == 'There are no new harvesting jobs'):
                pass

    def _gather_queue(self, num_jobs=1):

        for job in xrange(num_jobs):
            # Pop one item off the queue (the job id) and run the callback
            reply = self.gather_consumer.basic_get(
                queue='ckan.harvest.gather.test')

            # Make sure something was sent to the gather queue
            assert reply[2], 'Empty gather queue'

            # Send the item to the gather callback, which will call the
            # harvester gather_stage
            queue.gather_callback(self.gather_consumer, *reply)

    def _fetch_queue(self, num_objects=1):

        for _object in xrange(num_objects):
            # Pop item from the fetch queues (object ids) and run the callback,
            # one for each object created
            reply = self.fetch_consumer.basic_get(
                queue='ckan.harvest.fetch.test')

            # Make sure something was sent to the fetch queue
            assert reply[2], 'Empty fetch queue, the gather stage failed'

            # Send the item to the fetch callback, which will call the
            # harvester fetch_stage and import_stage
            queue.fetch_callback(self.fetch_consumer, *reply)

    def _run_full_job(self, harvest_source_id, num_jobs=1, num_objects=1):

        # Create new job for the source
        self._create_harvest_job(harvest_source_id)

        # Run the job
        self._run_jobs(harvest_source_id)

        # Handle the gather queue
        self._gather_queue(num_jobs)

        # Handle the fetch queue
        self._fetch_queue(num_objects)

    def test_harvest_create(self):

        # Mock the GET request to get the file
        httpretty.register_uri(httpretty.GET, self.mock_url,
                               body=self.remote_file)

        # The harvester will try to do a HEAD request first so we need to mock
        # this as well
        httpretty.register_uri(httpretty.HEAD, self.mock_url,
                               status=405)

        harvest_source = self._create_harvest_source()

        self._run_full_job(harvest_source['id'], num_objects=2)

        # Check that two datasets were created
        fq = "+type:dataset harvest_source_id:{0}".format(harvest_source['id'])
        results = h.call_action('package_search', {}, fq=fq)

        eq_(results['count'], 2)

        for result in results['results']:
            assert result['title'] in ('Example dataset 1',
                                       'Example dataset 2')

    def test_harvest_update(self):

        # Mock the GET request to get the file
        httpretty.register_uri(httpretty.GET, self.mock_url,
                               body=self.remote_file)

        # The harvester will try to do a HEAD request first so we need to mock
        # this as well
        httpretty.register_uri(httpretty.HEAD, self.mock_url,
                               status=405)

        harvest_source = self._create_harvest_source()

        # First run, will create two datasets as previously tested
        self._run_full_job(harvest_source['id'], num_objects=2)

        # Run the jobs to mark the previous one as Finished
        self._run_jobs()

        # Mock an update in the remote file
        new_file = self.remote_file.replace('Example dataset 1',
                                            'Example dataset 1 (updated)')
        httpretty.register_uri(httpretty.GET, self.mock_url,
                               body=new_file)

        # Run a second job
        self._run_full_job(harvest_source['id'], num_objects=2)

        # Check that we still have two datasets
        fq = "+type:dataset harvest_source_id:{0}".format(harvest_source['id'])
        results = h.call_action('package_search', {}, fq=fq)

        eq_(results['count'], 2)

        # Check that the dataset was updated
        for result in results['results']:
            assert result['title'] in ('Example dataset 1 (updated)',
                                       'Example dataset 2')

    def test_harvest_delete(self):

        # Mock the GET request to get the file
        httpretty.register_uri(httpretty.GET, self.mock_url,
                               body=self.remote_file)

        # The harvester will try to do a HEAD request first so we need to mock
        # this as well
        httpretty.register_uri(httpretty.HEAD, self.mock_url,
                               status=405)

        harvest_source = self._create_harvest_source()

        # First run, will create two datasets as previously tested
        self._run_full_job(harvest_source['id'], num_objects=2)

        # Run the jobs to mark the previous one as Finished
        self._run_jobs()

        # Mock a deletion in the remote file
        new_file = '''<?xml version="1.0" encoding="utf-8" ?>
        <rdf:RDF
         xmlns:dct="http://purl.org/dc/terms/"
         xmlns:dcat="http://www.w3.org/ns/dcat#"
         xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <dcat:Catalog rdf:about="https://data.some.org/catalog">
          <dcat:dataset>
            <dcat:Dataset rdf:about="https://data.some.org/catalog/datasets/1">
              <dct:title>Example dataset 1</dct:title>
            </dcat:Dataset>
          </dcat:dataset>
        </dcat:Catalog>
        </rdf:RDF>
        '''
        httpretty.register_uri(httpretty.GET, self.mock_url,
                               body=new_file)

        # Run a second job
        self._run_full_job(harvest_source['id'], num_objects=2)

        # Check that we only have one dataset
        fq = "+type:dataset harvest_source_id:{0}".format(harvest_source['id'])
        results = h.call_action('package_search', {}, fq=fq)

        eq_(results['count'], 1)

        eq_(results['results'][0]['title'], 'Example dataset 1')
