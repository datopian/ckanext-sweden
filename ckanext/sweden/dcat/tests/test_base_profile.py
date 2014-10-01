import nose

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace

from ckanext.sweden.dcat.profiles import RDFProfile

from ckanext.sweden.dcat.tests.test_base_parser import _default_graph


eq_ = nose.tools.eq_

DCT = Namespace("http://purl.org/dc/terms/")
TEST = Namespace("http://test.org/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")


class TestBaseRDFProfile(object):

    def test_datasets(self):

        p = RDFProfile(_default_graph())

        eq_(len([d for d in p._datasets()]), 3)

    def test_datasets_none_found(self):

        p = RDFProfile(Graph())

        eq_(len([d for d in p._datasets()]), 0)

    def test_distributions(self):

        p = RDFProfile(_default_graph())

        for dataset in p._datasets():
            if str(dataset) == 'http://example.org/datasets/1':
                eq_(len([d for d in p._distributions(dataset)]), 2)
            elif str(dataset) == 'http://example.org/datasets/2':
                eq_(len([d for d in p._distributions(dataset)]), 1)
            elif str(dataset) == 'http://example.org/datasets/3':
                eq_(len([d for d in p._distributions(dataset)]), 0)

    def test_object_value(self):

        p = RDFProfile(_default_graph())

        value = p._object_value(URIRef('http://example.org/datasets/1'),
                                DCT.title)

        assert isinstance(value, unicode)
        eq_(value, 'Test Dataset 1')

    def test_object_value_not_found(self):

        p = RDFProfile(_default_graph())

        value = p._object_value(URIRef('http://example.org/datasets/1'),
                                DCT.unknown_property)

        eq_(value, None)

    def test_object_int(self):

        p = RDFProfile(_default_graph())

        p.g.add((URIRef('http://example.org/datasets/1'),
                 TEST.some_number,
                 Literal('23')))

        value = p._object_value_int(URIRef('http://example.org/datasets/1'),
                                    TEST.some_number)

        assert isinstance(value, int)
        eq_(value, 23)

    def test_object_int_not_found(self):

        p = RDFProfile(_default_graph())

        value = p._object_value_int(URIRef('http://example.org/datasets/1'),
                                    TEST.some_number)

        eq_(value, None)

    def test_object_int_wrong_value(self):

        p = RDFProfile(_default_graph())

        p.g.add((URIRef('http://example.org/datasets/1'),
                 TEST.some_number,
                 Literal('Not an intger')))

        value = p._object_value_int(URIRef('http://example.org/datasets/1'),
                                    TEST.some_number)

        eq_(value, None)

    def test_object_list(self):

        p = RDFProfile(_default_graph())

        p.g.add((URIRef('http://example.org/datasets/1'),
                 DCAT.keyword,
                 Literal('space')))
        p.g.add((URIRef('http://example.org/datasets/1'),
                 DCAT.keyword,
                 Literal('moon')))

        value = p._object_value_list(URIRef('http://example.org/datasets/1'),
                                     DCAT.keyword)

        assert isinstance(value, list)
        assert isinstance(value[0], unicode)
        eq_(len(value), 2)
        eq_(sorted(value), ['moon', 'space'])

    def test_object_list_not_found(self):

        p = RDFProfile(_default_graph())

        value = p._object_value_list(URIRef('http://example.org/datasets/1'),
                                     TEST.some_list)

        assert isinstance(value, list)
        eq_(value, [])
