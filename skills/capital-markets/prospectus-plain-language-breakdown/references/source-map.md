# Source Map — prospectus-plain-language-breakdown

Every statement in the breakdown must cite a page in one of the sources below, ranked. See
the shared platform services in [`docs/SHARED-SERVICES.md`](../../../../docs/SHARED-SERVICES.md).

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed statutory prospectus / offering document** (and SAI where incorporated) | Authoritative text for every topic; controlling on conflict | Read-only (document-intelligence) |
| 2 | **Summary prospectus / KIID** for the same security + effective date | Headline breakdown, with cross-references to the statutory document | Read-only (document-intelligence) |
| 3 | **Approved-source retrieval** (filed-form / SAI retrieval) | Pulling incorporated-by-reference sections (SAI, statement of operations) | Read-only |
| 4 | **Reference/entity data** | Issuer/security identity resolution only (never disclosure content) | Read-only |

Never let marketing material, a fact sheet, or a user assertion stand in for the filed
document. If the summary and statutory documents conflict, cite both and treat the
**statutory document as controlling**; stop for human review if the conflict is material.

## Citation format

Each plain-language statement carries a page citation of the form `{doc}:p{page}` — e.g.
`prospectus:p12` or `SAI:p4` — and, where a topic spans pages, a `source_pages` list, e.g.
`[12, 13]`. The machine-readable output stores the citation and page list per topic section;
the narrative references the page inline where a fact is stated. A statement with no page to
cite is a **gap**, not a summary line.

## Freshness / effective dates

- Every document carries an **effective/filing date**; the breakdown states it and labels a
  document that is out of its update cycle (e.g., a fund prospectus is typically updated
  annually) as potentially superseded — it does not silently treat stale text as current.
- **Incorporated by reference**: a summary prospectus/KIID incorporates the statutory
  prospectus and SAI. When the referenced target is unavailable, cite the cross-reference and
  state that full detail lives in the referenced document; do not paraphrase unread text.
- Share-class-specific figures are cited to the page and class; never carry a figure across
  share classes.

## Least-privilege operations (deployment)

- `document.get(document_id)` → parsed prospectus with sections + page ranges (bounded size).
- `document.get_incorporated(document_id, target)` → SAI/statutory section by reference.
- `refdata.resolve(issuer|security)` → issuer/security identity only.
All read-only, deterministic schemas, durable `breakdown_id`, below the fixed timeout. No
network calls in this repository — scripts operate on de-identified JSON fixtures under
`evals/files/`.
