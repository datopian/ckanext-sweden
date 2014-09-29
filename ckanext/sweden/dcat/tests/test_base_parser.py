import nose

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import Namespace, RDF

from ckanext.sweden.dcat.parsers import RDFParser, RDFParserException

DCT = Namespace("http://purl.org/dc/terms/")
TEST = Namespace("http://test.org/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")

eq_ = nose.tools.eq_


class TestBaseRDFParser(object):

    def _default_graph(self):

        g = Graph()

        dataset1 = URIRef("http://example.org/datasets/1")
        g.add((dataset1, RDF.type, DCAT.Dataset))
        g.add((dataset1, DCT.title, Literal('Test Dataset 1')))

        distribution1_1 = URIRef("http://example.org/datasets/1/ds/1")
        g.add((distribution1_1, RDF.type, DCAT.Distribution))
        distribution1_2 = URIRef("http://example.org/datasets/1/ds/2")
        g.add((distribution1_2, RDF.type, DCAT.Distribution))

        g.add((dataset1, DCAT.distribution, distribution1_1))
        g.add((dataset1, DCAT.distribution, distribution1_2))

        dataset2 = URIRef("http://example.org/datasets/2")
        g.add((dataset2, RDF.type, DCAT.Dataset))
        g.add((dataset2, DCT.title, Literal('Test Dataset 2')))

        distribution2_1 = URIRef("http://example.org/datasets/2/ds/1")
        g.add((distribution2_1, RDF.type, DCAT.Distribution))
        g.add((dataset2, DCAT.distribution, distribution2_1))

        dataset3 = URIRef("http://example.org/datasets/3")
        g.add((dataset3, RDF.type, DCAT.Dataset))
        g.add((dataset3, DCT.title, Literal('Test Dataset 3')))

        return g

    def test_datasets(self):

        p = RDFParser()

        p.g = self._default_graph()

        eq_(len([d for d in p._datasets()]), 3)

    def test_datasets_none_found(self):

        p = RDFParser()

        p.g = Graph()

        eq_(len([d for d in p._datasets()]), 0)

    def test_distributions(self):

        p = RDFParser()

        p.g = self._default_graph()

        for dataset in p._datasets():
            if str(dataset) == 'http://example.org/datasets/1':
                eq_(len([d for d in p._distributions(dataset)]), 2)
            elif str(dataset) == 'http://example.org/datasets/2':
                eq_(len([d for d in p._distributions(dataset)]), 1)
            elif str(dataset) == 'http://example.org/datasets/3':
                eq_(len([d for d in p._distributions(dataset)]), 0)

    def test_object_value(self):

        p = RDFParser()

        p.g = self._default_graph()

        value = p._object_value(URIRef('http://example.org/datasets/1'),
                                DCT.title)

        assert isinstance(value, unicode)
        eq_(value, 'Test Dataset 1')

    def test_object_value_not_found(self):

        p = RDFParser()

        p.g = self._default_graph()

        value = p._object_value(URIRef('http://example.org/datasets/1'),
                                DCT.unknown_property)

        eq_(value, None)

    def test_object_int(self):

        p = RDFParser()

        p.g = self._default_graph()

        p.g.add((URIRef('http://example.org/datasets/1'),
                 TEST.some_number,
                 Literal('23')))

        value = p._object_value_int(URIRef('http://example.org/datasets/1'),
                                    TEST.some_number)

        assert isinstance(value, int)
        eq_(value, 23)

    def test_object_int_not_found(self):

        p = RDFParser()

        p.g = self._default_graph()

        value = p._object_value_int(URIRef('http://example.org/datasets/1'),
                                    TEST.some_number)

        eq_(value, None)

    def test_object_int_wrong_value(self):

        p = RDFParser()

        p.g = self._default_graph()

        p.g.add((URIRef('http://example.org/datasets/1'),
                 TEST.some_number,
                 Literal('Not an intger')))

        value = p._object_value_int(URIRef('http://example.org/datasets/1'),
                                    TEST.some_number)

        eq_(value, None)

    def test_object_list(self):

        p = RDFParser()

        p.g = self._default_graph()

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

        p = RDFParser()

        p.g = self._default_graph()

        value = p._object_value_list(URIRef('http://example.org/datasets/1'),
                                     TEST.some_list)

        assert isinstance(value, list)
        eq_(value, [])

    def test_parse(self):

        p = RDFParser()

        nose.tools.assert_raises(NotImplementedError, p.parse, '')

    def test_parse_data(self):

        data = '''<?xml version="1.0" encoding="utf-8" ?>
        <rdf:RDF
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
        <rdfs:SomeClass rdf:about="http://example.org">
            <rdfs:label>Some label</rdfs:label>
        </rdfs:SomeClass>
        </rdf:RDF>
        '''

        p = RDFParser()

        eq_(len(p.g), 0)

        p._parse_data(data)

        eq_(len(p.g), 2)

    def test_parse_data_different_format(self):

        data = '''
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        <http://example.org> a rdfs:SomeClass ;
            rdfs:label "Some label" .
        '''

        p = RDFParser()

        eq_(len(p.g), 0)

        p._parse_data(data, _format='n3')

        eq_(len(p.g), 2)

    def test_parse_data_raises_on_parse_error(self):

        p = RDFParser()

        data = 'Wrong data'

        nose.tools.assert_raises(RDFParserException, p._parse_data, '')

        nose.tools.assert_raises(RDFParserException, p._parse_data, data)

        nose.tools.assert_raises(RDFParserException, p._parse_data, data,
                                 _format='n3',)
