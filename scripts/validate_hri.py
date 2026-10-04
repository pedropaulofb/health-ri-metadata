"""Validate metadata using a separately trusted SNOMED CT named-class hierarchy."""
import argparse
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, RDFS, URIRef

SHAPES = Path(__file__).resolve().parents[1] / 'Formalisation(shacl)/Core/ReusedCommunityStandards/health-ri-vocabulary/health-ri-metadata-shapes.ttl'


def validation_graph(data, hierarchy):
    """Use only the caller-supplied trusted hierarchy as subclass evidence.

    No OWL/RDFS inference or imports are applied. Submitted subclass statements
    are excluded, including any produced by the vocabulary's range inference.
    The caller must select an authoritative SNOMED release/export independently
    of the submitted data; this function cannot authenticate that input.
    """
    graph = Graph()
    for triple in data:
        if triple[1] != RDFS.subClassOf:
            graph.add(triple)
    for subject, _, parent in hierarchy.triples((None, RDFS.subClassOf, None)):
        if isinstance(subject, URIRef) and isinstance(parent, URIRef):
            graph.add((subject, RDFS.subClassOf, parent))
    return graph


def validate_metadata(data, hierarchy):
    return validate(validation_graph(data, hierarchy),
                    shacl_graph=Graph().parse(SHAPES), inference='none',
                    do_owl_imports=False, meta_shacl=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path, help='Submitted metadata RDF file')
    parser.add_argument('--snomed-hierarchy', type=Path, required=True,
                        help='Trusted RDF export of SNOMED named-class rdfs:subClassOf edges')
    args = parser.parse_args()
    try:
        conforms, _, report = validate_metadata(Graph().parse(args.data),
                                                Graph().parse(args.snomed_hierarchy))
    except Exception as exc:
        parser.exit(2, f'Validation failed: {exc}\n')
    print(report)
    return 0 if conforms else 1


if __name__ == '__main__':
    raise SystemExit(main())
