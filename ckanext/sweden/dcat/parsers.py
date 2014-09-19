# DCAT parsers, Work in progress

# Dev stuff, will probably get removed
import fileinput

import json

import rdflib
from rdflib.namespace import Namespace, RDF

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")


class RDFParser(object):

    def __init__(self):

        self.g = rdflib.Graph()

    def _datasets(self):
        '''
        Returns all DCAT datasets on the graph
        '''
        for dataset in self.g.subjects(RDF.type, DCAT.Dataset):
            yield dataset

    def _distributions(self, dataset):

        for distribution in self.g.objects(dataset, DCAT.distribution):
            yield distribution

    def _object(self, subject, predicate):

        for o in self.g.objects(subject, predicate):
            return unicode(o)
        return None

    def _object_int(self, subject, predicate):

        object_value = self._object(subject, predicate)
        if object_value:
            try:
                return int(object_value)
            except ValueError:
                pass
        return None

    def _object_list(self, subject, predicate):

        return [unicode(o) for o in self.g.objects(subject, predicate)]

    def parse(self, contents, _format=None):

        raise NotImplemented


class DCATAPParser(RDFParser):

    def parse(self, contents, _format=None):

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
                value = self._object(dataset, predicate)
                if value:
                    ckan_dict[key] = value

            # Tags

            keywords = self._object_list(dataset, DCAT.keyword) or []
            for keyword in keywords:
                ckan_dict['tags'].append({'name': keyword})

            # Extras

            #  Simple values
            for key, predicate in (
                    ('dcat_issued', DCT.issued),
                    ('dcat_modified', DCT.modified),
                    ('guid', DCT.identifier),  # backwards compatibility
                    ('dcat_identifier', DCT.identifier),
                    ('dcat_alternate_identifier', ADMS.identifier),
                    ('dcat_version', ADMS.version),
                    ('dcat_version_notes', ADMS.versionNotes),
                    ('dcat_frequency', DCT.accrualPeriodicity),
                    ('dcat_spatial', DCT.spatial),
                    ('dcat_temporal', DCT.temporal),

                    ):
                value = self._object(dataset, predicate)
                if value:
                    ckan_dict['extras'].append({'key': key, 'value': value})

            #  Lists
            for key, predicate in (
                    ('language', DCT.language),
                    ('dcat_theme', DCAT.theme),
                    ('dcat_conforms_to', DCAT.conformsTo),
                    ):
                values = self._object_list(dataset, predicate)
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
                        ('dcat_licence', DCT.license),
                        ):
                    value = self._object(distribution, predicate)
                    if value:
                        resource_dict[key] = value

                resource_dict['url'] = (self._object(distribution, DCAT.accessURL) or
                                        self._object(distribution, DCAT.downloadURL))

                size = self._object_int(distribution, DCAT.byteSize)
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

    contents = ''
    for line in fileinput.input():
        contents += line

    parser = DCATAPParser()
    ckan_datasets = parser.parse(contents)

    print json.dumps(ckan_datasets)
