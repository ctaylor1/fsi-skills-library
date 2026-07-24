# Source Map — credit-terms-covenant-extractor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Controlled credit document** (indenture, credit agreement, offering memorandum, prospectus, term sheet) via document-intelligence | The authoritative text of every extracted term | Read-only |
| 2 | **Document-intelligence** layer | Page/section/clause locators and candidate spans for each term | Read-only |
| 3 | **Entity resolution** | Resolve the issuer/instrument (CUSIP/ISIN/deal) so the extraction binds to the right security | Read-only |
| 4 | **Controlled content library** (field taxonomy, seniority ranking, ambiguity-marker list) | Versioned normalization rules the scripts apply | Read-only |

The document is the position of record. If the document-intelligence candidate span and the
underlying page text conflict, the **page text governs** and the item is flagged
`needs_review`. Never substitute a summary, a prior deal's terms, or an analyst's recollection
for the document text. A term with no page-level citation is **not** extracted — it fails
closed.

## Document scope

Controlled, final credit documents only (execution or filed versions). Drafts, redlines, and
marketing decks are out of scope; if supplied, record `doc_version` and flag every field
`needs_review` because terms are not yet fixed.

## Citation format

`{doc_id}:p.{page} {locator}` — e.g. `OM-2026-0417:p.55 Sec. 4.07 Limitation on Restricted
Payments`. **Every** extracted or needs_review field cites its page and, where available, the
section/clause locator. Page number is mandatory (see `scripts/validate_output.py`).

## Freshness / effective dates / versioning

- The document is a **versioned contract**: `doc_id`, `doc_version` (draft/execution/filed),
  and `effective_date` are recorded on the output so an extraction is reproducible and
  re-runnable against the exact source.
- The normalization rule set (field taxonomy, seniority ranking, ambiguity markers) is
  versioned in the controlled content library; the `extraction_id` binds the output to the
  inputs so re-running the same document with the same rules reproduces the fields.
- Amendments/supplemental indentures supersede the base document for the amended terms; run a
  fresh extraction against the amended text and record the governing `doc_id`.

## Durable identifiers

`extraction_id = ctce-{doc_id}-{effective_date}-NNNN` binds the output to the exact document,
version, and effective date. It is durable across re-runs and is the artifact downstream
skills reference (see [handoffs.md](handoffs.md)).

## Least-privilege operations (deployment)

- `docintel.terms(doc_id, fields)` → candidate spans with page/section locators.
- `entity.resolve(issuer|cusip|isin)` → canonical issuer/instrument identity.
- `content.rules('credit-terms', version)` → field taxonomy, seniority ranking, markers.
All read-only, deterministic, durable `extraction_id`, below the fixed timeout; page long
documents as resumable stages. No writes, no network retries.
