# oppnadata-new-orgs - Automatic organizations creation for Öppnadata.se

This script provides an automated way of creating organizations remotely on the
Öppnadata.se site. It also handles the setting up of the DCAT harvesting for
each of them and inviting the administrator user to the new organization.

## Install

The script does not depend on CKAN or ckanext-sweden, but it does require some external
Python libraries. You can install them on the same virtualenv as ckanext-sweden is
installed or create a new virtualenv. In any case, to install the requirements on a
virtualenv, activate it and run:

    pip install ckanapi slugify chardet

To install the requirements globally, just run: 

    sudo pip install ckanapi slugify chardet


## Running the script

The script is run like this (we will assume that you are at the same directory as the
script):

    python oppnadata-new-orgs.py -h

This will show the help regarding the command.

The script targets the Öppnadata.se CKAN instance (http://oppnadata.se) by default,
but this can be changed (for example for testing purposes), either by setting the
`CKAN_OPPNADATA_SITE_URL` environment variable or by passing the `-s` option:


    python oppnadata-new-orgs.py -s http://sweden.staging.ckanhosted.com

You will need to provide an [API key](http://docs.ckan.org/en/latest/api/index.html#authentication-and-api-keys)
for a sysadmin user account on the CKAN site you are targeting. The API key can
be provided setting the `CKAN_OPPNADATA_API_KEY` environment variable or by
passing the `-a` option:

    python oppnadata-new-orgs.py -s http://sweden.staging.ckanhosted.com -a a72fd4d1-3c...

If called without any more parameters, the script will prompt for the organization
name, its URL, and optionally for the URL of the DCAT datasets and an email for the administrator
user:


    python oppnadata-new-orgs.py
    Organization Title: Test organization  
    Organization Url (Website): http://example.com
    Dcat Datasets Url [http://example.com/datasets/dcat.rdf]:
    Admin User Email []: admin@example.com

You can also pass all these parameters via command line arguments:

    python oppnadata-new-orgs.py -t "Test organization" -u "http://example.com" -d "http://example.com/dcat.rdf" -e "admin@example.com"

But you probably want to create several organizations in bulk rather than one by one. To do so, check the next section.


## Providing a list of organizations

The scripts supports creating several organizations in bulk, by reading all parameters from a [CSV](http://en.wikipedia.org/wiki/Comma-separated_values) file.

You provide the path to the CSV file as the first parameter of the script:

    python oppnadata-new-orgs.py /path/to/organizations.csv

The CSV file should have the following structure (note that the header names must be exactly as shown):

| name             | url                             | dcat_url                                   | admin_email        |
|------------------|---------------------------------|--------------------------------------------|--------------------|
|Protokollen       | http://www.protokollen.net      | http://www.protokollen.net/datasets/dcat   |                    | 
|Svenska kyrkan    | https://svenskakyrkan.se        | https://api.svenskakyrkan.se/datasets/dcat | admin1@example.com |
|Bokföringsnämnden | http://www.bfn.se               |                                            | admin2@example.com | 
|Försäkringskassan | http://www.forsakringskassan.se |                                            |                    |

The first two columns (`name` and `url`) are mandatory. If `dcat_url` is not provided it will be assumed than
the DCAT datasets are located at `{org_url}/datasets/dcat.rdf`. If no `admin_email` is provided, no invites will
be sent to users to become administrators of the orgnaization.

There are two example CSV files (with different encodings) on this folder.

## Full usage

```
python oppnadata-new-orgs.py -h
usage: oppnadata-new-orgs.py [-h] [-a API_KEY] [-s SITE] [-t ORG_TITLE]
                             [-u ORG_URL] [-d DCAT_URL] [-e ADMIN_EMAIL] [-q]
                             [file]

Creates a new organization on Oppnadata.se and perform admin processes. These
include sending invites to admin users if email addresses are provided,
creating a new harvest source for the organization DCAT endpoint and create
the first harvest job for importing its datasets. If the API key is not
provided it will be read from CKAN_OPPNADATA_API_KEY. The site to create the
organizations on defaults to http://oppnadata.se. This can be changed using
the -s option or setting the CKAN_OPPNADATA_SITE_URL env var. If the rest of
parameters are not provided you will be prompt for them.

positional arguments:
  file                  CSV file with organizations to be created (see docs
                        for format). If omitted -t and -u must be provided.

optional arguments:
  -h, --help            show this help message and exit
  -a API_KEY, --api_key API_KEY
                        A valid sysadmin key for Oppnadata.se
  -s SITE, --site SITE  URL of the site to target (defaults to
                        http://oppnadata.se)
  -t ORG_TITLE, --org_title ORG_TITLE
                        Title of the organization to be created
  -u ORG_URL, --org_url ORG_URL
                        Url of the organization to be created
  -d DCAT_URL, --dcat_url DCAT_URL
                        Url of the DCAT datasets. Defaults to
                        {org_url}/datasets/dcat.rdf
  -e ADMIN_EMAIL, --admin_email ADMIN_EMAIL
                        Email address of the admin user
  -q, --quiet           Don't output any messages
```
