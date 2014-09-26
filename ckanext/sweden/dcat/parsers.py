# DCAT parsers, Work in progress

# Dev stuff, will probably get removed
import sys
import argparse

import json

import rdflib
from rdflib.namespace import Namespace, RDF

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")


class RDFParser(object):
    '''
    A base class for RDF parsers based on rdflib

    Contains helper functions for parsing the graph
    '''

    def __init__(self):

        self.g = rdflib.Graph()

    def _datasets(self):
        '''
        Generator that returns all DCAT datasets on the graph

        Yields rdflib.term.URIRef objects that can be used on graph lookups
        and queries
        '''
        for dataset in self.g.subjects(RDF.type, DCAT.Dataset):
            yield dataset

    def _distributions(self, dataset):
        '''
        Generator that returns all DCAT distributions on a particular dataset

        Yields rdflib.term.URIRef objects that can be used on graph lookups
        and queries
        '''
        for distribution in self.g.objects(dataset, DCAT.distribution):
            yield distribution

    def _object_value(self, subject, predicate):
        '''
        Given a subject and a predicate, returns the value of the object

        Both subject and predicate must be rdflib.term.URIRef objects

        If found, the unicode representation is returned, else None
        '''
        for o in self.g.objects(subject, predicate):
            return unicode(o)
        return None

    def _object_value_int(self, subject, predicate):
        '''
        Given a subject and a predicate, returns the value of the object as an
        integer

        Both subject and predicate must be rdflib.term.URIRef objects

        If the value can not be parsed as intger, returns None
        '''
        object_value = self._object_value(subject, predicate)
        if object_value:
            try:
                return int(object_value)
            except ValueError:
                pass
        return None

    def _object_value_list(self, subject, predicate):
        '''
        Given a subject and a predicate, returns a list with all the values of
        the objects

        Both subject and predicate must be rdflib.term.URIRef objects

        If no values found, returns an empty string
        '''
        return [unicode(o) for o in self.g.objects(subject, predicate)]

    def parse(self, data=None, _format=None):
        '''
        Parses and RDF graph serialization and returns CKAN dataset dicts

        Data is a string with the serialized RDF graph (eg RDF/XML, N3
        ... ). By default RF/XML is expected. The optional parameter _format
        can be used to tell rdflib otherwise.

        If no data is provided it's assumed that the graph property
        (`g`) has been set directly.

        Different profiles should implement this method and return a list of
        CKAN dataset dicts (something that can be passed to `package_create`
        or `package_update`).

        '''
        raise NotImplementedError


class EuroDCATAPParser(RDFParser):
    '''
    An RDF parser based on the DCAT-AP for data portals in Europe

    More information and specification:

    https://joinup.ec.europa.eu/asset/dcat_application_profile

    '''

    def parse(self, contents=None, _format=None):

        if contents:
            self.g.parse(data=contents, format=_format)

        ckan_datasets = []

        for dataset in self._datasets():
            ckan_dict = {
                'tags': [],
                'extras': [],
                'resources': []
            }

            # Basic fields
            for key, predicate in (
                    ('title', DCT.title),
                    ('notes', DCT.description),
                    ('url', DCAT.landingUrl),
                    ):
                value = self._object_value(dataset, predicate)
                if value:
                    ckan_dict[key] = value

            # Tags

            keywords = self._object_value_list(dataset, DCAT.keyword) or []
            for keyword in keywords:
                ckan_dict['tags'].append({'name': keyword})

            # Extras

            #  Simple values
            for key, predicate in (
                    ('dcat_issued', DCT.issued),
                    ('dcat_modified', DCT.modified),
                    ('dcat_identifier', DCT.identifier),
                    ('dcat_alternate_identifier', ADMS.identifier),
                    ('dcat_version', ADMS.version),
                    ('dcat_version_notes', ADMS.versionNotes),
                    ('dcat_frequency', DCT.accrualPeriodicity),
                    ('dcat_spatial', DCT.spatial),
                    ('dcat_temporal', DCT.temporal),

                    ):
                value = self._object_value(dataset, predicate)
                if value:
                    ckan_dict['extras'].append({'key': key, 'value': value})

            #  Lists
            for key, predicate in (
                    ('language', DCT.language),
                    ('dcat_theme', DCAT.theme),
                    ('dcat_conforms_to', DCAT.conformsTo),
                    ):
                values = self._object_value_list(dataset, predicate)
                if values:
                    ckan_dict['extras'].append({'key': key,
                                                'value': json.dumps(values)})

            # Dataset URI (explicitly show the missing ones)
            dataset_uri = (unicode(dataset)
                           if isinstance(dataset, rdflib.term.URIRef)
                           else None)
            ckan_dict['extras'].append({'key': 'uri', 'value': dataset_uri})

            # Resources
            for distribution in self._distributions(dataset):

                resource_dict = {}

                #  Simple values
                for key, predicate in (
                        ('name', DCT.title),
                        ('description', DCT.description),
                        ('format', DCT.format),
                        ('mimetype', DCAT.mediaType),
                        ('dcat_download_url', DCAT.downloadURL),
                        ('dcat_issued', DCT.issued),
                        ('dcat_modified', DCT.modified),
                        ('dcat_status', ADMS.status),
                        ('dcat_rights', DCT.rights),
                        ('dcat_license', DCT.license),
                        ):
                    value = self._object_value(distribution, predicate)
                    if value:
                        resource_dict[key] = value

                resource_dict['url'] = (self._object_value(distribution, DCAT.accessURL) or
                                        self._object_value(distribution, DCAT.downloadURL))

                size = self._object_value_int(distribution, DCAT.byteSize)
                if size is not None:
                        resource_dict['size'] = size

                # Distribution URI (explicitly show the missing ones)
                resource_dict['uri'] = (unicode(distribution)
                                        if isinstance(distribution,
                                                      rdflib.term.URIRef)
                                        else None)

                ckan_dict['resources'].append(resource_dict)

            ckan_datasets.append(ckan_dict)

        return ckan_datasets


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Parse DCAT RDF graphs to CKAN dataset JSON objects')
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('-f', '--format',
                        help='''Serialization format (as understood by rdflib)
                                eg: xml, n3 ...'). Defaults to \'xml\'.''')
    parser.add_argument('-p', '--pretty',
                        action='store_true',
                        help='Make the output more human readable')

    args = parser.parse_args()

    contents = args.file.read()

    parser = DCATAPParser()
    ckan_datasets = parser.parse(contents, _format=args.format)

    indent = 4 if args.pretty else None
    print json.dumps(ckan_datasets, indent=indent)
