from rdflib.namespace import Namespace

from ckanext.dcat.profiles import RDFProfile


DCT = Namespace("http://purl.org/dc/terms/")


class SwedishDCATAPProfile(RDFProfile):
    '''
    An RDF profile for the Swedish DCAT-AP recommendation for data portals

    It requires the European DCAT-AP profile (`euro_dcat_ap`)
    '''

    def parse_dataset(self, dataset_dict, dataset_ref):

        # Spatial label
        spatial = self._object(dataset_ref, DCT.spatial)
        if spatial:
            spatial_label = self.g.label(spatial)
            if spatial_label:
                dataset_dict['extras'].append({'key': 'spatial_text',
                                               'value': str(spatial_label)})

        return dataset_dict
