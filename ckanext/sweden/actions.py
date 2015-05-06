import json

from pylons import config

import ckan.logic.converters as converters
import ckan.plugins.toolkit as toolkit


@toolkit.side_effect_free
def dcat_organization_list(context, data_dict):
    '''Return dcat details for organizations in the site.

    Return an array of objects (one per CKAN organization).
    '''

    data_dict = {
        'all_fields': True,
        'include_extras': True
    }
    organizations = toolkit.get_action('organization_list')(context=context,
                                                            data_dict=data_dict)

    dcat_org_list = []
    for org in organizations:
        dcat_org_data = {'id': org['id']}

        # set original_dcat_metadata_url
        harvest_list = _harvest_list_for_org(context, org['id'])
        if not harvest_list:
            continue
        harvest_url = harvest_list[0].get('url', '')
        dcat_org_data.update({'original_dcat_metadata_url': harvest_url})

        # set uri
        extras = org.get('extras', [])
        uri = next((i['value'] for i in extras if i['key'] == 'uri'), '')
        dcat_org_data.update({'uri': uri})

        # set dcat_metadata_url
        dcat_metadata_url = (config.get('ckan.site_url').rstrip('/') +
                             toolkit.url_for('dcat_organization',
                                             _id=org['name'],
                                             _format='rdf'))
        dcat_org_data.update({'dcat_metadata_url': dcat_metadata_url})

        dcat_org_list.append(dcat_org_data)

    return dcat_org_list


@toolkit.side_effect_free
def dcat_validation(context, data_dict):
    '''
    Return the validation errors for the last harvest job of the organization
    harvest source.
    '''
    org_id = toolkit.get_or_bust(data_dict, 'id')
    try:
        id = converters.convert_group_name_or_id_to_id(org_id, context)
    except toolkit.Invalid:
        raise toolkit.ObjectNotFound

    harvest_list = _harvest_list_for_org(context, id)
    if harvest_list:
        harvest_source_id = harvest_list[0].get('id', '')
        source_status = toolkit.get_action('harvest_source_show_status')(context=context,
                                                                         data_dict={'id': harvest_source_id})
        last_job = source_status.get('last_job', None)
        if last_job:
            last_job_report = toolkit.get_action('harvest_job_report')(context=context,
                                                                       data_dict={'id': last_job['id']})

        gather_errors = last_job_report.get('gather_errors', [])
        gather_errors_list = []
        for error in gather_errors:
            try:
                message = json.loads(error.get('message'))
            except ValueError:
                message = error.get('message', '')

            gather_errors_list.append(message)

        return gather_errors_list
    else:
        return None


def _harvest_list_for_org(context, org_id):
    '''
    Return a list of harvest datasets with `owner_org` that corresponds with
    `org_id`.

    (This list should really only have one member.)
    '''
    harvest_dict = {
        'fq': 'owner_org:"{org_id}" type:"harvest"'.format(org_id=org_id)
    }
    harvest_search = toolkit.get_action('package_search')(context=context,
                                                          data_dict=harvest_dict)
    return harvest_search.get('results', [])
