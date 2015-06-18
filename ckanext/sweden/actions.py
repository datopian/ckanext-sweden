import json

from pylons import config

import ckan.logic.converters as converters
import ckan.plugins.toolkit as toolkit


@toolkit.side_effect_free
def dcat_organization_list(context, data_dict):
    '''Return dcat details for organizations in the site.

    Return an array of objects (one per CKAN organization).
    '''

    toolkit.check_access('dcat_organization_list', context, data_dict)

    data_dict = {
        'all_fields': True,
        'include_extras': True
    }
    organizations = toolkit.get_action('organization_list')(context=context,
                                                            data_dict=data_dict)

    dcat_org_list = []
    for org in organizations:
        dcat_org_data = {
            'id': org['id'],
            'dcat_validation_result': "{host}{path}".format(
                host=config.get('ckan.site_url').rstrip('/'),
                path=toolkit.url_for('dcat_validation',
                                     _id=org['name'])),
            'dcat_validation': None,
            'dcat_validation_date': None,
        }

        dcat_validation = toolkit.get_action('dcat_validation')(context,
                                                                {'id': org['id']})
        if dcat_validation and dcat_validation.get('result'):
            dcat_org_data['dcat_validation'] = dcat_validation['result']['errors'] == 0
            dcat_org_data['dcat_validation_date'] = dcat_validation['last_validation']
        else:
            dcat_org_data['dcat_validation'] = None
            dcat_org_data['dcat_validation_date'] = None

        # set original_dcat_metadata_url
        harvest_list = _harvest_list_for_org(context, org['id'])
        if not harvest_list:
            continue
        harvest_url = harvest_list[0].get('url', '')
        dcat_org_data.update({'original_dcat_metadata_url': harvest_url})

        # set uri
        extras = org.get('extras', [])
        url = next((i['value'] for i in extras if i['key'] == 'url'), '')
        dcat_org_data.update({'url': url})

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

    toolkit.check_access('dcat_validation', context, data_dict)

    org_id = toolkit.get_or_bust(data_dict, 'id')
    try:
        id = converters.convert_group_name_or_id_to_id(org_id, context)
    except toolkit.Invalid:
        raise toolkit.ObjectNotFound

    harvest_list = _harvest_list_for_org(context, id)
    if harvest_list:
        harvest_package = harvest_list[0]
        harvest_source_id = harvest_package.get('id', '')
        source_status = toolkit.get_action('harvest_source_show_status')(
            context=context, data_dict={'id': harvest_source_id})

        return_obj = {
            'url': harvest_package['url'],
            'last_validation': None,
            'result': None,
        }
        last_job = source_status.get('last_job', None)
        if last_job:

            return_obj['last_validation'] = last_job['gather_finished']

            last_job_report = toolkit.get_action('harvest_job_report')(context={'ignore_auth': True},
                                                                       data_dict={'id': last_job['id']})

            gather_errors = last_job_report.get('gather_errors', [])
            gather_errors_list = []
            error_count = 0
            warning_count = 0
            for error in gather_errors:
                try:
                    message = json.loads(error.get('message'))
                except ValueError:
                    message = error.get('message', '')
                else:
                    if message.get('errors') and type(message.get('errors')) is list:
                        error_count += len(message.get('errors'))
                    if message.get('warnings') and type(message.get('warnings')) is list:
                        warning_count += len(message.get('warnings'))

                gather_errors_list.append(message)

            result_obj = {
                'errors': error_count,
                'warnings': warning_count,
                'resources': gather_errors_list
            }

            return_obj['result'] = result_obj

        return return_obj
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


# TODO: This overrides the core `user_invite` action to be able to customize
# the email sent, until #2465 gets merged and this extension targets a CKAN
# version that uses it. Once this happens, all this can go
import random
from ckan import logic
from ckan import new_authz as authz
from ckan.lib import mailer
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.base import render_jinja2


def user_invite(context, data_dict):
    '''Invite a new user.

    You must be authorized to create group members.

    :param email: the email of the user to be invited to the group
    :type email: string
    :param group_id: the id or name of the group
    :type group_id: string
    :param role: role of the user in the group. One of ``member``, ``editor``,
        or ``admin``
    :type role: string

    :returns: the newly created yser
    :rtype: dictionary
    '''
    toolkit.check_access('user_invite', context, data_dict)

    schema = context.get('schema',
                         logic.schema.default_user_invite_schema())
    data, errors = toolkit.navl_validate(data_dict, schema, context)
    if errors:
        raise toolkit.ValidationError(errors)

    model = context['model']
    group = model.Group.get(data['group_id'])
    if not group:
        raise toolkit.ObjectNotFound()

    name = logic.action.create._get_random_username_from_email(data['email'])
    password = str(random.SystemRandom().random())
    data['name'] = name
    data['password'] = password
    data['state'] = model.State.PENDING
    user_dict = toolkit.get_action('user_create')(context, data)
    user = model.User.get(user_dict['id'])
    member_dict = {
        'username': user.id,
        'id': data['group_id'],
        'role': data['role']
    }
    toolkit.get_action('group_member_create')(context, member_dict)

    if group.is_organization:
        group_dict = toolkit.get_action('organization_show')(context,
            {'id': data['group_id']})
    else:
        group_dict = toolkit.get_action('group_show')(context,
            {'id': data['group_id']})

    mailer.create_reset_key(user)

    # Email body
    group_type = (toolkit._('organization') if group_dict['is_organization']
                  else toolkit._('group'))
    role = data['role']
    extra_vars = {
        'reset_link': mailer.get_reset_link(user),
        'site_title': config.get('ckan.site_title'),
        'site_url': config.get('ckan.site_url'),
        'user_name': user.name,
        'role_name': authz.roles_trans().get(role, toolkit._(role)),
        'group_type': group_type,
        'group_title': group_dict.get('title'),
    }

    # NOTE: This template is translated
    body = render_jinja2('emails/invite_user.txt', extra_vars)
    subject = toolkit._('Invite for {site_title}').format(
        site_title=config.get('ckan.site_title'))

    mailer.mail_user(user, subject, body)

    return model_dictize.user_dictize(user, context)
