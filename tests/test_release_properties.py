"""Compatibility and vocabulary integration regressions."""
import importlib.util
import json
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, SKOS, URIRef

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'Formalisation(shacl)/Core'
HRI = Namespace('https://w3id.org/health-ri/metadata-vocabulary#')
SH = Namespace('http://www.w3.org/ns/shacl#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
SCT = Namespace('http://snomed.info/id/')
DATASET = URIRef('https://example.org/dataset')
REFERENCE = CORE / 'ReusedCommunityStandards/health-ri-vocabulary'


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_registrations_and_definitions():
    sync = module('sync_release_properties')
    sync.synchronize(check=True)
    manifest = json.loads((ROOT / 'Documents/next-release-properties.json').read_text())
    vocab = Graph().parse(REFERENCE / 'health-ri-metadata-vocabulary-v0.4.1.ttl')
    for path in sync.TARGETS:
        graph = Graph().parse(path)
        for p in manifest['properties']:
            subject = URIRef('http://data.health-ri.nl/core/p2/DatasetShape#' + p['label'].replace(' ', '-'))
            assert (subject, SH.path, URIRef(p['iri'])) in graph
            # Descriptions cannot accidentally acquire stricter constraints.
            assert set(graph.predicates(subject)) == {RDF.type, SH.path, SH.name, SH.description, RDFS.seeAlso}
            if p['iri'].startswith(str(HRI)):
                assert p['definition'] == str(vocab.value(URIRef(p['iri']), SKOS.definition))
                assert vocab.value(URIRef(p['iri']), RDFS.domain) == DCAT.Dataset
            assert p['cardinality'] == '0..n'


@pytest.mark.parametrize('path', sorted((ROOT / 'Formalisation(shacl)').rglob('*.ttl')),
                         ids=lambda p: str(p.relative_to(ROOT)))
def test_turtle_artifacts_parse(path):
    # Includes archived module files; an empty graph is valid Turtle.
    Graph().parse(path)


def data(prop=None, value=None):
    graph = Graph()
    graph.add((DATASET, RDF.type, DCAT.Dataset))
    if prop:
        graph.add((DATASET, prop, value))
    return graph


def optional_check(graph, hierarchy=None):
    return module('validate_hri').validate_metadata(graph, hierarchy if hierarchy is not None else Graph())[0]


def test_optional_and_repeatable_health_conditions():
    assert optional_check(data())
    graph = data(HRI.healthConditionOfInterest, SCT['22298006'])
    graph.add((SCT['22298006'], RDF.type, SKOS.Concept))
    icd = URIRef('http://id.who.int/icd/release/10/2019/I21')
    graph.add((DATASET, HRI.healthConditionOfInterest, icd))
    graph.add((icd, RDF.type, SKOS.Concept))
    assert optional_check(graph)


@pytest.mark.parametrize('value,typed', [
    (Literal('myocardial infarction'), False),
    (SCT['22298006'], False),
    (URIRef('https://example.org/condition'), True),
])
def test_optional_health_checks_reject_invalid_values(value, typed):
    graph = data(HRI.healthConditionOfInterest, value)
    if typed:
        graph.add((value, RDF.type, SKOS.Concept))
    assert not optional_check(graph)


def test_anatomy_root_transitive_evidence_and_no_concept_typing():
    graph = data(HRI.anatomicalLocationCovered, SCT['91723000'])
    assert optional_check(graph)
    graph.add((DATASET, HRI.anatomicalLocationCovered, SCT['39607008']))
    hierarchy = Graph()
    # Synthetic edges test path handling, not authoritative terminology membership.
    hierarchy.add((SCT['39607008'], RDFS.subClassOf, SCT['123456']))
    hierarchy.add((SCT['123456'], RDFS.subClassOf, SCT['91723000']))
    assert optional_check(graph, hierarchy)
    assert not optional_check(graph)


def test_submitted_anatomical_evidence_is_not_trusted():
    graph = data(HRI.anatomicalLocationCovered, SCT['39607008'])
    graph.add((SCT['39607008'], RDFS.subClassOf, SCT['91723000']))
    assert not optional_check(graph)


@pytest.mark.parametrize('filename', ['PiecesShape/Dataset.ttl', 'FairDataPointShape/Dataset.ttl',
                                     'ValidationShape/HRI-Datamodel-shapes.ttl'])
def test_new_example_core_validation(filename):
    conforms, _, report = validate(str(CORE / 'Example-Data/example-dataset-hri.ttl'),
                                   shacl_graph=str(CORE / filename), meta_shacl=True)
    assert conforms, report


def test_new_example_optional_validation():
    assert optional_check(Graph().parse(CORE / 'Example-Data/example-dataset-hri.ttl'))


def test_descriptive_additions_preserve_extension_acceptance():
    # Previously unknown extension values must not become core violations.
    graph = Graph().parse(CORE / 'Example-Data/example-dataset.ttl')
    subject = next(graph.subjects(RDF.type, DCAT.Dataset))
    graph.add((subject, HRI.healthConditionOfInterest, Literal('legacy extension')))
    conforms, _, report = validate(graph, shacl_graph=str(CORE / 'FairDataPointShape/Dataset.ttl'), meta_shacl=True)
    assert conforms, report
    assert not optional_check(graph)
