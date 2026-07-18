# Source Map — submission-intake-triager

## Source hierarchy (field-typed authority)

Authority is per **document type**, not a single global rank. The canonical value for a
field is taken from the highest-authority document that reported it; disagreements are always
surfaced (never resolved silently).

| Field(s) | Authoritative document | Then | Access |
| -------- | ---------------------- | ---- | ------ |
| `total_insured_value` (and schedule values) | **SOV spreadsheet** (`sov_spreadsheet`) | ACORD → email → PDF → other | Read-only |
| `prior_loss_ratio`, `loss_count` | **Loss run** (`loss_run`) | ACORD → email → PDF → other | Read-only |
| Application data (`insured_name`, `insured_state`, `class_code`, `effective_date`, `annual_revenue`, `building_count`, `catastrophe_zone`) | **ACORD application** (`acord`) | SOV → loss run → email → PDF → other | Read-only |

The broker cover email and free-text PDFs are **supporting**: usable as corroboration or to
fill a gap, but they never override the SOV, loss run, or ACORD for the fields above.

Never substitute a broker assertion for the underlying document. If the SOV and ACORD (or an
email) disagree on TIV, cite both and flag the mismatch for the underwriter.

## Citation format

`{doc_type}:{source_ref}` — e.g.
`sov_spreadsheet:sub=SUB-2026-0442;doc=D-2;field=total_insured_value`. Every appetite
finding and every reconciliation row cites the specific document/field it came from.

## Platform services used (not reimplemented here)

- **Document intelligence** (OCR + ACORD/PDF/SOV extraction) — produces the `extracted_fields`
  this skill consumes; the skill does not re-OCR.
- **Entity resolution** — resolve insured/producer/location entities.
- **Approved-source retrieval** — the versioned **appetite config** (states, excluded
  classes, capacity, loss-ratio and catastrophe thresholds).
- **Permission / approval broker** — separates read from any external follow-up delivery.

See [../../../docs/SHARED-SERVICES.md](../../../docs/SHARED-SERVICES.md).

## Freshness / effective dates

- The **appetite config** is a versioned contract; the output records the `config_version`
  used so a triage is reproducible.
- The submission `received_date` and the requested `effective_date` are both recorded; a
  stale submission (effective date in the past) is a data-quality flag for the underwriter.

## Least-privilege operations (deployment)

- `docintel.extract(doc_id)` → normalized fields + `source_ref` (read-only).
- `policyadmin.lookup(insured|producer)` → producer/insured context (read-only).
- `appetite.get(line_of_business, version)` → states, classes, thresholds (read-only).
- `exposure.enrich(location)` → third-party catastrophe-zone tags (read-only).

All read-only, deterministic, durable `triage_id`, below the fixed timeout; page long
document sets as resumable stages. No mutating operation is bound by this skill.
