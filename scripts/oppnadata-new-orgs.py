#!/usr/bin/env python
'''
Check

    python oppnadata-new-orgs -h

Or if it's in your path:

    oppnadata-new-orgs -h

Requires ckanapi, slugify and chardet:

    pip install ckanapi slugify chardet

TODO:

* Docs


'''

import sys
import os
import argparse
import csv

requires = []
try:
    import ckanapi
except ImportError:
    requires.append('ckanapi')
try:
    import slugify
except ImportError:
    requires.append('slugify')
try:
    import chardet
except ImportError:
    requires.append('chardet')

if requires:
    print('Missing requirements, please install them by running:\n    ' +
          'pip install {0}'.format(' '.join(requires)))
    sys.exit(1)


site_env_var_name = 'CKAN_OPPNADATA_SITE_URL'
api_key_env_var_name = 'CKAN_OPPNADATA_API_KEY'


global quiet


def _out(msg):
    if not quiet:
        print(msg)


def _check_unicode(text, min_confidence=0.5):
    if not text:
        return
    try:
        text = text.decode('utf-8')
    except UnicodeDecodeError:
        guess = chardet.detect(text)
        if guess["confidence"] < min_confidence:
            raise UnicodeDecodeError
        text = unicode(text, guess["encoding"])
        text = text.encode('utf-8')
    return text


def create_org(ckan, org_title, org_url, dcat_url=None, admin_email=None,
               quiet=False):

    org_created = False
    source_created = False
    email_sent = False

    org_title = _check_unicode(org_title)
    org_url = _check_unicode(org_url)
    dcat_url = _check_unicode(dcat_url)
    admin_email = _check_unicode(admin_email)

    org_url = org_url.rstrip('/')

    try:
        org_title_output = org_title.encode('utf-8')
    except UnicodeDecodeError:
        org_title_output = org_title

    # Compute org name
    org_name = slugify.slugify(org_title)

    # Check if org exists
    try:
        org = ckan.action.organization_show(id=org_name)
        _out('Organization "{0}" already exists, skipping creation...'.format(
            org_title_output))
    except ckanapi.NotFound:
        # Create org
        params_org = {
            'title': org_title,
            'name': org_name,
            'url': org_url,
        }
        org = ckan.action.organization_create(**params_org)
        org_created = True
        _out('Organization "{0}" created'.format(org_title_output))

    # Create harvest source
    try:
        source = ckan.action.harvest_source_show(id=org['name'])
        _out(('Harvest Source "{0}" already exists, skipping creation' +
             '...').format(org_title_output))
    except ckanapi.NotFound:
        dcat_url = dcat_url or '{0}/datasets/dcat.rdf'.format(org_url)
        params_source = {
            'title': org['title'],
            'name': org['name'],
            'url': dcat_url,
            'owner_org': org['id'],
            'frequency': 'WEEKLY',
            'source_type': 'dcat_rdf',
        }
        source = ckan.action.harvest_source_create(**params_source)
        source_created = True
        _out('Created organization "{0}"'.format(org_title_output))

        # Create a new harvest job
        params = {
            'source_id': source['id'],
        }
        source = ckan.action.harvest_job_create(**params)
        _out('Harvest Source "{0}" created'.format(org_title_output))

    # Admin user
    if admin_email:
        # Check if user is already an admin or has been invited
        user_exists = False
        for org_user in org.get('users', []):
            user = ckan.action.user_show(id=org_user['name'])
            if user.get('email') == admin_email:
                user_exists = True
                _out(('User {0} already an admin of "{1}", skipping invite' +
                     '...').format(admin_email, org_title_output))
                break

        # Send user invite
        if not user_exists:
            params_invite = {
                'email': admin_email,
                'group_id': org['id'],
                'role': 'admin',
            }

            user = ckan.action.user_invite(**params_invite)
            email_sent = True
            _out('Admin user for "{0}" created, and invite email sent'.format(
                admin_email))

    return org_created, source_created, email_sent

if __name__ == '__main__':

    description = '''
Creates a new organization on Oppnadata.se and perform admin processes.
These include sending invites to admin users if email addresses are provided,
creating a new harvest source for the organization DCAT endpoint and create
the first harvest job for importing its datasets. If the API key is not
provided it will be read from {0}. The site to create the organizations on
defaults to http://oppnadata.se. This can be changed using the -s option or
setting the {1} env var. If the rest of parameters are not provided you will
be prompt for them.
'''.format(api_key_env_var_name, site_env_var_name)

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'),
                        help='CSV file with organizations to be created (see' +
                             ' docs for format). If omitted -t and -u must' +
                             ' be provided.')
    parser.add_argument('-a', '--api_key',
                        help='A valid sysadmin key for Oppnadata.se')
    parser.add_argument('-s', '--site',
                        default='http://oppnadata.se',
                        help='URL of the site to target (defaults to ' +
                             'http://oppnadata.se)')
    parser.add_argument('-t', '--org_title',
                        help='Title of the organization to be created')
    parser.add_argument('-u', '--org_url',
                        help='Url of the organization to be created')
    parser.add_argument('-d', '--dcat_url',
                        help='Url of the DCAT datasets. Defaults to ' +
                             '{org_url}/datasets/dcat.rdf')
    parser.add_argument('-e', '--admin_email',
                        help='Email address of the admin user')
    parser.add_argument('-q', '--quiet',
                        action='store_true',
                        default=False,
                        help='Don\'t output any messages')

    args = parser.parse_args()

    api_key = args.api_key
    if not api_key:
        api_key = os.environ.get(api_key_env_var_name)
        if not api_key:
            _out('No API key provided explicitly or on {0}'.format(
                 api_key_env_var_name))
            sys.exit(1)

    site = os.environ.get(site_env_var_name)
    if not site:
        site = args.site

    ckan = ckanapi.RemoteCKAN(site, apikey=api_key)

    quiet = args.quiet

    counts = {
        'orgs': 0,
        'sources': 0,
        'emails': 0,
    }
    orgs = []
    if args.file:
        with args.file as f:
            reader = csv.DictReader(f)
            for row in reader:

                org_title = row['name']
                org_url = row['url']
                dcat_url = row['dcat_url']
                admin_email = row['admin_email']

                orgs.append(row)
    else:

        def _check_arg(args, var, prompt, default=None):
            if getattr(args, var):
                return getattr(args, var)
            if default is None:
                msg = '{0}:'.format(prompt.title())
            else:
                msg = '{0} [{1}]:'.format(prompt.title(), default)
            var = raw_input(msg)
            if not var and default is None:
                _out('Please provide a value for the {0}'.format(prompt))
                sys.exit(1)
            elif not var:
                var = default
            return var

        if args.org_title and args.org_url:
            org_title = args.org_title
            org_url = args.org_url
            default_dcat_url = '{0}/datasets/dcat.rdf'.format(
                org_url.rstrip('/'))
            dcat_url = args.dcat_url or default_dcat_url
            admin_email = args.admin_email
        else:
            org_title = _check_arg(args, 'org_title', 'Organization title')
            org_url = _check_arg(args, 'org_url', 'Organization URL (website)')
            default_dcat_url = '{0}/datasets/dcat.rdf'.format(
                org_url.rstrip('/'))
            dcat_url = _check_arg(args, 'org_url', 'DCAT datasets URL',
                                  default_dcat_url)
            admin_email = _check_arg(args, 'admin_email', 'Admin user email',
                                     '')

        orgs.append({'name': org_title, 'url': org_url,
                     'dcat_url': dcat_url, 'admin_email': admin_email})

    for org in orgs:
        try:
            org_created, source_created, email_sent = create_org(
                ckan,
                org['name'], org['url'], org['dcat_url'], org['admin_email'])
            counts['orgs'] += int(org_created)
            counts['sources'] += int(source_created)
            counts['emails'] += int(email_sent)
        except ckanapi.NotAuthorized:
            _out('Authorization error. Are you using a sysadmin API key ' +
                 'for the relevant site?')
            sys.exit(1)

    msg = ('Done: ' +
           '{orgs} organizations created, ' +
           '{sources} sources created, ' +
           '{emails} admin emails sent').format(**counts)

    _out(msg)
