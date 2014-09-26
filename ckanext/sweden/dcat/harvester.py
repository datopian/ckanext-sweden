import json
import uuid
import logging

import ckan.plugins as p
import ckan.model as model
import ckan.logic as logic

from ckanext.harvest.model import HarvestObject, HarvestObjectExtra
# TODO: refactor caknext-dcat so lxml is not needed
from ckanext.dcat.harvesters import DCATHarvester

from ckanext.sweden.dcat.parsers import EuroDCATAPParser


log = logging.getLogger(__name__)


class RDFDCATHarvester(DCATHarvester):

    def info(self):
        return {
            'name': 'dcat_rdf',
            'title': 'Generic DCAT RDF Harvester',
            'description': 'Harvester for DCAT datasets from an RDF graph'
        }

    def _get_guid(self, dataset_dict, source_url=None):
        '''
        Try to get a unique identifier for a harvested dataset

        It will be the first found of:
         * URI (rdf:about)
         * dcat:identifier
         * Source URL + Dataset name
         * Dataset name

         The last two are obviously not optimal, as depend on title, which
         might change.

         Returns None if no guid could be decided.
        '''

        guid = None

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'uri':
                return extra['value']

        for extra in dataset_dict.get('extras', []):
            if extra['key'] == 'dcat_identifier':
                return extra['value']

        if dataset_dict.get('name'):
            guid = dataset_dict['name']
            if source_url:
                guid = source_url.rstrip('/') + '/' + guid

        return guid

    def _get_existing_dataset(self, guid):
        '''
        Checks if a dataset with a certain guid extra already exists

        Returns a dict as the ones returned by package_show
        '''

        datasets = model.Session.query(model.Package.id) \
                                .join(model.PackageExtra) \
                                .filter(model.PackageExtra.key=='guid') \
                                .filter(model.PackageExtra.value==guid) \
                                .filter(model.Package.state=='active') \
                                .all()

        if not datasets:
            return None
        elif len(datasets) > 1:
            log.error('Found more than one dataset with the same guid: {0}'.format(guid))

        return p.toolkit.get_action('package_show')({}, {'id': datasets[0][0]})

    def _mark_datasets_for_deletion(self, guids_in_source, harvest_job):
        '''
        Given a list of guids in the remote source, checks which in the DB
        need to be deleted

        To do so it queries all guids in the DB for this source and calculates
        the difference.

        For each of these creates a HarvestObject with the dataset id, marked
        for deletion.

        Returns a list with the ids of the Harvest Objects to delete.
        '''

        object_ids = []

        # Get all previous current guids and dataset ids for this source
        query = model.Session.query(HarvestObject.guid, HarvestObject.package_id) \
                             .filter(HarvestObject.current==True) \
                             .filter(HarvestObject.harvest_source_id==harvest_job.source.id)

        guid_to_package_id = {}
        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = guid_to_package_id.keys()

        # Get objects/datasets to delete (ie in the DB but not in the source)
        guids_to_delete = set(guids_in_db) - set(guids_in_source)

        # Create a harvest object for each of them, flagged for deletion
        for guid in guids_to_delete:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                extras=[HarvestObjectExtra(key='status',
                                                           value='delete')])

            # Mark the rest of objects for this guid as not current
            model.Session.query(HarvestObject) \
                         .filter_by(guid=guid) \
                         .update({'current': False}, False)
            obj.save()
            object_ids.append(obj.id)

        return object_ids

    def gather_stage(self, harvest_job):

        log.debug('In RDFDCATHarvester gather_stage')

        # Get file contents
        url = harvest_job.source.url

        content = self._get_content(url, harvest_job, 1)

        # TODO: store content?

        if not content:
            return None

        parser = EuroDCATAPParser()
        # TODO: format
        datasets = parser.parse(content)

        if not datasets:
            self._save_gather_error('No DCAT datasets could be found', harvest_job)
            return False

        guids_in_source = []
        object_ids = []
        for dataset in datasets:
            if not dataset.get('name'):
                dataset['name'] = self._gen_new_name(dataset['title'])

            # Try to get a unique identifier for the harvested dataset
            guid = self._get_guid(dataset)
            if not guid:
                log.error('Could not get a unique identifier for dataset: {0}'.format(dataset))
                continue

            dataset['extras'].append({'key': 'guid', 'value': guid})
            guids_in_source.append(guid)

            obj = HarvestObject(guid=guid, job=harvest_job,
                                content=json.dumps(dataset))


            obj.save()
            object_ids.append(obj.id)

        # Check if some datasets need to be deleted
        object_ids_to_delete = self._mark_datasets_for_deletion(guids_in_source, harvest_job)

        object_ids.extend(object_ids_to_delete)

        return object_ids

    def fetch_stage(self, harvest_object):
        # Nothing to do here
        return True

    def import_stage(self, harvest_object):

        log.debug('In RDFDCATHarvester import_stage')

        status = self._get_object_extra(harvest_object, 'status')
        if status == 'delete':
            # Delete package
            context = {'model': model, 'session': model.Session,
                       'user': self._get_user_name(), 'ignore_auth': True}

            p.toolkit.get_action('package_delete')(context, {'id': harvest_object.package_id})
            log.info('Deleted package {0} with guid {1}'.format(harvest_object.package_id,
                                                                harvest_object.guid))
            return True

        if harvest_object.content is None:
            self._save_object_error('Empty content for object {0}'.format(harvest_object.id),
                                    harvest_object, 'Import')
            return False

        try:
            dataset = json.loads(harvest_object.content)
        except ValueError:
            self._save_object_error('Could not parse content for object {0}'.format(harvest_object.id),
                                    harvest_object, 'Import')
            return False

        # Get the last harvested object (if any)
        previous_object = model.Session.query(HarvestObject) \
                                       .filter(HarvestObject.guid==harvest_object.guid) \
                                       .filter(HarvestObject.current==True) \
                                       .first()

        # Flag previous object as not current anymore
        if previous_object:
            previous_object.current = False
            previous_object.add()

        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.add()

        context = {
            'user': self._get_user_name(),
            'return_id_only': True,
            'ignore_auth': True,
        }

        # Check if a dataset with the same guid exists
        existing_dataset = self._get_existing_dataset(harvest_object.guid)

        if existing_dataset:
            # Don't change the dataset name even if the title has
            dataset['name'] = existing_dataset['name']
            dataset['id'] = existing_dataset['id']

            # Save reference to the package on the object
            harvest_object.package_id = dataset['id']
            harvest_object.add()

            try:
                p.toolkit.get_action('package_update')(context, dataset)
            except p.toolkit.ValidationError, e:
                self._save_object_error('Update validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False

            log.info('Updated dataset %s', dataset['name'])

        else:

            package_schema = logic.schema.default_create_package_schema()
            context['schema'] = package_schema

            # We need to explicitly provide a package ID
            dataset['id'] = unicode(uuid.uuid4())
            package_schema['id'] = [unicode]

            # Save reference to the package on the object
            harvest_object.package_id = dataset['id']
            harvest_object.add()

            # Defer constraints and flush so the dataset can be indexed with
            # the harvest object id (on the after_show hook from the harvester
            # plugin)
            model.Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
            model.Session.flush()

            try:
                p.toolkit.get_action('package_create')(context, dataset)
            except p.toolkit.ValidationError, e:
                self._save_object_error('Create validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False

            log.info('Created dataset %s', dataset['name'])


        model.Session.commit()

        return True
