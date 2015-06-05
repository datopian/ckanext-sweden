from pylons import config
from nose import tools as nosetools
import ckan.logic as logic
try:
    import ckan.tests.factories as factories
    import ckan.tests.helpers as helpers
except ImportError:
    # CKAN 2.3
    import ckan.new_tests.factories as factories
    import ckan.new_tests.helpers as helpers


assert_equal = nosetools.assert_equal
assert_true = nosetools.assert_true
assert_raises = nosetools.assert_raises


class TestDcatOrganizationList(helpers.FunctionalTestBase):

    def test_dcat_organization_list_no_orgs(self):
        '''
        dcat_organization_list action returns empty results when no orgs
        exists.
        '''
        dcat_org_list = helpers.call_action('dcat_organization_list')
        assert_equal(dcat_org_list, [])

    def test_dcat_organization_list_has_keys(self):
        '''
        dcat_organization_list action returns list with the correct keys.
        '''
        org = factories.Organization(url='http://example.com/url')
        factories.Dataset(owner_org=org['id'],
                          type='harvest',
                          source_type='dcat_rdf',
                          url='http://example.com/source')
        dcat_org_list = helpers.call_action('dcat_organization_list')

        assert_equal(len(dcat_org_list), 1)
        org = dcat_org_list[0]
        assert_true('url' in org)
        assert_true('original_dcat_metadata_url' in org)
        assert_true('id' in org)
        assert_true('dcat_metadata_url' in org)

    def test_dcat_organization_list_org_has_correct_values(self):
        '''
        dcat_organization_list action returns list of one result with correct
        values.
        '''
        org = factories.Organization(url='http://example.com/url')
        factories.Dataset(owner_org=org['id'],
                          type='harvest',
                          source_type='dcat_rdf',
                          url='http://example.com/source')
        dcat_org_list = helpers.call_action('dcat_organization_list')

        assert_equal(len(dcat_org_list), 1)
        dcat_org = dcat_org_list[0]
        assert_equal(dcat_org['id'], org['id'])
        assert_equal(dcat_org['original_dcat_metadata_url'], u'http://example.com/source')
        assert_equal(dcat_org['url'], u'http://example.com/url')
        assert_equal(dcat_org['dcat_metadata_url'],
                               '{0}/organization/{1}/dcat.rdf'.format(
                                   config.get('ckan.site_url').rstrip('/'),
                                   org['name']))

    def test_dcat_organization_list_no_orgs_without_harvest_pair(self):
        '''
        dcat_organization_list shouldn't list orgs that don't have a
        counterpart harvest dataset.
        '''
        factories.Organization(url='http://example.com/url')
        dcat_org_list = helpers.call_action('dcat_organization_list')

        assert_equal(len(dcat_org_list), 0)


class TestOrgSchema(object):

    @classmethod
    def setup_class(cls):
        helpers.reset_db()

    def teardown(cls):
        helpers.reset_db()

    def test_url_field_create(self):
        url = 'http://org1.com'
        factories.Organization(name='org1', url=url)

        org = helpers.call_action('organization_show', id='org1')

        assert_equal(org['url'], url)

    def test_url_field_create_strips_backslash(self):
        url = 'http://org1.com/'
        factories.Organization(name='org1', url=url)

        org = helpers.call_action('organization_show', id='org1')

        assert_equal(org['url'], url.rstrip('/'))

    def test_url_field_update(self):
        url = 'http://org1.com'
        factories.Organization(name='org1', url=url)
        user = factories.User()

        helpers.call_action('organization_update', id='org1',
                            context={'user': user['name']},
                            name='org1',
                            url='http://org1.com/new')

        org = helpers.call_action('organization_show', id='org1')
        assert_equal(org['url'], 'http://org1.com/new')

    def test_url_field_update_other_field(self):
        url = 'http://org1.com'
        factories.Organization(name='org1', url=url)
        user = factories.User()

        helpers.call_action('organization_update',
                            context={'user': user['name']},
                            id='org1',
                            name='org1',
                            desc='org desc',
                            url=url)

        org = helpers.call_action('organization_show', id='org1')
        assert_equal(org['url'], url)

    def test_url_field_cant_update_to_existing(self):
        url = 'http://org1.com'
        factories.Organization(name='org1', url=url)

        assert_raises(logic.ValidationError, helpers.call_action, 'organization_update',
                      name='org2', url=url)
