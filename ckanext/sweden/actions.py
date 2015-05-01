from pylons import config
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
        harvest_dict = {
            'fq': 'owner_org:"{org_id}" type:"harvest"'.format(org_id=org['id'])
        }
        harvest_search = toolkit.get_action('package_search')(context=context,
                                                              data_dict=harvest_dict)
        harvest_list = harvest_search.get('results', [])
        if not harvest_list:
            continue
        harvest_url = harvest_list[0].get('url', '') if harvest_list else None
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
