import json

import ckan.plugins.toolkit as toolkit

from ckanext.dcat.utils import CONTENT_TYPES


class DCATController(toolkit.BaseController):

    def read_organization(self, _id, _format='rdf'):

        try:
            org_dict = toolkit.get_action('organization_show')({}, {'id': _id})
        except toolkit.ObjectNotFound:
            toolkit.abort(404, toolkit._('Organization not found'))

        data_dict = {
            'fq': 'owner_org:{0}'.format(org_dict['id']),
            'format': _format,
            'page': toolkit.request.params.get('page'),
        }

        toolkit.response.headers.update(
            {'Content-type': CONTENT_TYPES[_format]})
        try:
            return toolkit.get_action('dcat_catalog_search')({}, data_dict)
        except toolkit.ValidationError, e:
            toolkit.abort(409, str(e))

    def organization_dcat_validation(self, _id):
        try:
            dcat_validation_dict = \
                toolkit.get_action('dcat_validation')({}, {'id': _id})
        except toolkit.ObjectNotFound:
            toolkit.abort(404, toolkit._('Organization not found'))

        toolkit.response.headers.update({'Content-type': 'application/json'})

        return json.dumps(dcat_validation_dict)
