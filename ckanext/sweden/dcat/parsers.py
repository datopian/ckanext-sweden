# DCAT parsers, Work in progress

# Dev stuff, will probably get removed
import fileinput
import json

import rdflib
from rdflib.namespace import Namespace

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

g = rdflib.Graph()


query_datasets = '''
SELECT ?dataset
WHERE {
    ?dataset a dcat:Dataset
}
'''

query_datasets2 = '''
SELECT ?dataset
WHERE {
    ?catalog dcat:dataset ?dataset
}
'''

query_distributions = '''
SELECT ?distribution
WHERE {
    ?dataset dcat:distribution ?distribution
}
'''


def _datasets():
    '''
    Returns all DCAT datasets on the graph
    '''

    datasets = [r.dataset for r in g.query(query_datasets)]

    if not datasets:

        datasets = [r.dataset for r in g.query(query_datasets2)]

    return datasets


def _distributions(dataset):

    for r in g.query(query_distributions, initBindings={'dataset': dataset}):
        yield r.distribution


def _object(subject, predicate):

    objects = [unicode(o) for o in g.objects(subject, predicate)]

    return objects[0] if objects else None


def _object_int(subject, predicate):

    object_value = _object(subject, predicate)
    if object_value:
        try:
            return int(object_value)
        except ValueError:
            pass
    return None


def _object_list(subject, predicate):

    objects = [unicode(o) for o in g.objects(subject, predicate)]

    return objects or []


def parse(contents):

    g.parse(data=contents)

    g.bind('dct', 'http://purl.org/dc/terms/')
    g.bind('dcat', 'http://www.w3.org/ns/dcat#')

    ckan_datasets = []
    for dataset in _datasets():

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
            value = _object(dataset, predicate)
            if value:
                ckan_dict[key] = value

        # Tags

        keywords = _object_list(dataset, DCAT.keyword) or []
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
            value = _object(dataset, predicate)
            if value:
                ckan_dict['extras'].append({'key': key, 'value': value})

        #  Lists
        for key, predicate in (
                ('language', DCT.language),
                ('dcat_theme', DCAT.theme),
                ('dcat_conforms_to', DCAT.conformsTo),
                ):
            values = _object_list(dataset, predicate)
            if values:
                ckan_dict['extras'].append({'key': key, 'value': values})

        # Dataset URI (explicitly show the missing ones)
        dataset_uri = (unicode(dataset)
                       if isinstance(dataset, rdflib.term.URIRef)
                       else None)
        ckan_dict['extras'].append({'key': 'uri', 'value': dataset_uri})

        # Resources
        for distribution in _distributions(dataset):

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
                value = _object(distribution, predicate)
                if value:
                    resource_dict[key] = value

            resource_dict['url'] = (_object(distribution, DCAT.accessURL) or
                                    _object(distribution, DCAT.downloadURL))

            size = _object_int(distribution, DCAT.byteSize)
            if size is not None:
                    resource_dict['size'] = size

            # Distribution URI (explicitly show the missing ones)
            resource_dict['uri'] = (unicode(distribution)
                                    if isinstance(distribution, rdflib.term.URIRef)
                                    else None)

            ckan_dict['resources'].append(resource_dict)

        ckan_datasets.append(ckan_dict)

        return ckan_datasets


if __name__ == '__main__':

    contents = ''
    for line in fileinput.input():
        contents += line

    ckan_datasets = parse(contents)

    print json.dumps(ckan_datasets)
