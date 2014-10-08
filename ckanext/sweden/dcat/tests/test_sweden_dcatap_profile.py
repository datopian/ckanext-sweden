import os

import nose

from ckanext.sweden.dcat.parsers import RDFParser

eq_ = nose.tools.eq_


class TestSwedenDCATAPProfile(object):

    def _get_file_contents(self, file_name):
        path = os.path.join(os.path.dirname(__file__),
                            '..', 'examples',
                            file_name)
        with open(path, 'r') as f:
            return f.read()

    def test_dataset_spatial_label(self):

        contents = self._get_file_contents('dataset_sweden.rdf')

        p = RDFParser(profiles=['euro_dcat_ap', 'sweden_dcat_ap'])

        p.parse(contents)

        datasets = [d for d in p.datasets()]

        eq_(len(datasets), 1)

        dataset = datasets[0]

        def _get_extra_value(key):
            v = [extra['value'] for extra in dataset['extras'] if extra['key'] == key]
            return v[0] if v else None

        eq_(_get_extra_value('spatial_text'), u'Stockholm')
