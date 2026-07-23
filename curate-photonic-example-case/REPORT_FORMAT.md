# Curation output contract

Each prepared candidate directory contains:

```text
source-snapshot.json
cleaning-plan.json
cleaning-report.json
sensitivity-report.json
validation-report.json
example-candidate.json
g3-review.md
payload/
```

## Cleaning report

Record:

- candidate ID, tool version, source URI, source tree hash, and timestamps;
- include/transform/exclude/blocked/needs-human-input decisions;
- source and target hashes for transformed files;
- fields added and their exact provenance;
- removed or unmapped structured fields;
- unresolved questions;
- license and sensitivity findings;
- schema and integrity results;
- recommended quality with rationale;
- a final source snapshot and `source_unchanged` result.

## G3 review

The reviewer confirms:

- the source case was not modified;
- staging matches the cleaning report;
- all references and hashes pass;
- execution and convergence evidence was not fabricated;
- license and sensitivity are known;
- the quality level and failure tags are correct;
- credentials and required absolute machine paths are absent;
- `example_id@version` is unused.

The decision records reviewer, timestamp, rationale, approved quality,
publication permission, and the SHA-256 of the exact staged candidate. Any
candidate change invalidates the decision.

If the source arrived with a prior human review, retain that review as
provenance. After cleaning, the reviewer must confirm a new G3 decision bound
to the normalized `example-candidate.json` hash. This confirmation may reference
the prior review instead of repeating its full scientific rationale.
