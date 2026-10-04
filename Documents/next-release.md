# Forthcoming minor release — draft

The final release number and publication date have not been assigned here.
The released baseline is upstream `master` at
`534b0d071b4136aaba6b2808f9927099956c3a7c` (v2.0.3).

## Optional dataset properties

The structured source for these additions is
[`next-release-properties.json`](next-release-properties.json). It supplements
`Metadata_CoreGenericHealth_v2.xlsx`; the workbook alone does not describe the
complete forthcoming release. The additions are not backported into that workbook
or its existing SHACL pipeline template. After generating legacy shapes from those
templates, run `python scripts/sync_release_properties.py` from the repository root.

| Property | Cardinality | Value |
|---|---|---|
| `hri:healthConditionOfInterest` | 0..n | IRI identifying a suitable SNOMED CT or ICD-10 concept, typed `skos:Concept` |
| `hri:anatomicalLocationCovered` | 0..n | SNOMED CT anatomical class IRI, root 91723000 or a subclass; no `skos:Concept` typing required |
| `dct:alternative` | 0..n | Literal alternative name |
| `dcat:landingPage` | 0..n | IRI identifying a landing-page document |
| `dct:provenance` | 0..n | Resource representing a provenance statement |

Here `hri` means `https://w3id.org/health-ri/metadata-vocabulary#`.
The two Health-RI properties use the definitions in
[vocabulary v0.4.1](https://w3id.org/health-ri/metadata-vocabulary/v0.4.1).
The pinned repository copy is available under
`Formalisation(shacl)/Core/ReusedCommunityStandards/health-ri-vocabulary/`.
The existing shapes use `hri` for `http://data.health-ri.nl/core/p2/`;
their generated additions therefore use full property IRIs to avoid collision.

Both Health-RI relations concern the dataset as a whole. Health conditions do not
assert participant diagnoses. Anatomical coverage does not link a particular body
site to a particular modality or data category. The anatomical range uses OWL Full
metamodeling, not OWL 2 DL. Range entailment is not trusted terminology evidence.

No equivalent-property or predecessor mapping has been asserted. Existing external
properties, IRIs, value forms and cardinalities remain supported as before.

## Validation and compatibility

Core shape registrations describe the new properties without adding constraints.
This deliberately preserves acceptance even for records that used these previously
unknown extensions. The semantic definitions and intended value forms above still
apply when using the properties. A passing core SHACL report does not prove correct
use of the new terms. No consumer migration is required by this implementation.

The source vocabulary's suggested checks are available as an **opt-in** validator:

```bash
python scripts/validate_hri.py metadata.ttl --snomed-hierarchy trusted-snomed.ttl
```

Use the same Python environment as the tests (`hatch run python ...` when using
Hatch). The hierarchy file must be an independently obtained, trusted SNOMED CT
release/export containing named-class `rdfs:subClassOf` edges. Record its release
and provenance in the validation process. An empty Turtle file suffices only when
no non-root anatomical values need checking. The example uses the anatomical root
so that it needs no downloaded terminology hierarchy.

The validator ignores subclass assertions supplied in metadata and does not load
the vocabulary's OWL axioms. Identifier patterns cannot confirm that a concept
exists, is active, or is clinically suitable. The validator cannot authenticate
the supplied hierarchy. Its conformance result is separate from core conformance.
Making these checks mandatory requires an explicit profile decision and a separate
compatibility assessment; do not silently enable them for existing consumers.

Example: `Formalisation(shacl)/Core/Example-Data/example-dataset-hri.ttl`.

## Existing development work retained

The current `develop` tree already includes Dataset and Distribution retention-period
usage clarifications, repository cleanup, and contributor/testing documentation
corrections. It has the same SHACL constraint graphs as released `master` before
the descriptive additions above. Dependency-update PRs are not merged by this work.
The alternative-title, landing-page and provenance rows originate from the upstream
documentation `v2.1` branch and are preserved in the structured addendum.

## Before publication

- Review the schema `develop` and documentation `v2.1` changes together.
- Run `hatch run test` and `python scripts/sync_release_properties.py --check`.
- In the documentation checkout, run its generator, tests, Bikeshed build and
  `python scripts/check_release_alignment.py /path/to/health-ri-metadata`.
- Resolve the existing schema/documentation cardinality discrepancies before making
  a blanket profile-conformance claim (notably Distribution title, issue #255, and Catalog dataset membership).
- Confirm the final schema version, date, vocabulary adoption and validation policy.
- Update `CITATION.cff` at release time; its current version/date describe the
  released v2.0.3 baseline, not the unpublished candidate.
- Merge schema through `develop` to `master` and publish the corresponding tag/release.
- Merge the reviewed documentation candidate to `main` in coordination with that
  release. This triggers the existing Pages publication model. Record both commit
  SHAs in the release notes; a schema tag alone does not deploy documentation.

No cross-repository write token, release creation, tag, or Pages setting change is
introduced by this preparation. Automation validates schema PRs, branch pushes and
version tags; documentation CI verifies regeneration and builds the candidate.
