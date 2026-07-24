# Source Map — financial-document-version-comparator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Controlled **document repository** (system of record) | Both document versions (structured) | Read-only |
| 2 | **Document-intelligence** | Section/heading/value extraction from source docs | Read-only |

Never edit or publish a version; cite every change to the section id and both version labels.

## Citation format
`{doc_id}:{section_id}@{versionA->versionB}` — e.g. `TS-4471:section-3.2@v2->v3`. Value changes
also cite the field name.

## Freshness / effective dates
- Compare two named versions of the **same** `doc_id`; refuse cross-document comparison.
- Record both version labels + as-of; flag a stale repository copy.

## Least-privilege operations (deployment)
- `docrepo.read(doc_id, version)` → structured sections/values — read-only.
Durable `comparison_id`; deterministic; no edit/publish.
