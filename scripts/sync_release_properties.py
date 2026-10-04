"""Register optional release properties without changing core conformance."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'Formalisation(shacl)/Core'
TARGETS = [CORE / p for p in (
    'PiecesShape/Dataset.ttl', 'FairDataPointShape/Dataset.ttl',
    'ValidationShape/HRI-Datamodel-shapes.ttl')]
START = '# BEGIN generated optional release properties\n'
END = '# END generated optional release properties\n'


def generated():
    source = json.loads((ROOT / 'Documents/next-release-properties.json').read_text())
    lines = [START.rstrip(), '# Source: Documents/next-release-properties.json',
             '# Descriptive registrations only; optional vocabulary checks are separate.']
    shape = 'http://data.health-ri.nl/core/p2/DatasetShape'
    for p in source['properties']:
        prop_shape = shape + '#' + p['label'].replace(' ', '-')
        lines += [f'<{shape}> sh:property <{prop_shape}> .',
                  f'<{prop_shape}> a sh:PropertyShape ;',
                  f'    sh:path <{p["iri"]}> ;',
                  f'    sh:name {json.dumps(p["label"])}@en ;',
                  f'    sh:description {json.dumps(p["definition"] + " " + p["usage"])}@en ;',
                  f'    rdfs:seeAlso <{p["source"]}> .', '']
    return '\n'.join(lines) + END


def synchronize(check=False):
    block = generated()
    stale = []
    for path in TARGETS:
        text = path.read_text()
        if START in text:
            before, rest = text.split(START, 1)
            _, after = rest.split(END, 1)
            expected = before + block + after
        else:
            expected = text.rstrip() + '\n\n' + block
        if text != expected:
            stale.append(str(path.relative_to(ROOT)))
            if not check:
                path.write_text(expected)
    if check and stale:
        raise SystemExit('Regenerate release registrations: ' + ', '.join(stale))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    synchronize(parser.parse_args().check)
