# Controls — valuation-reviewer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the review pack goes to the audit
  file, the valuation committee, or any system of record. Internal analytical use may be
  reviewer-sampled. The skill never posts a value or approves anything.

## Prohibited (fail closed)

- No **valuation sign-off**, **override / adjustment approval**, or statement that a mark
  **is** "correct / accurate / fair value". Findings and evidence only.
- No **posting, booking, or writing** of a value to the GL, subledger, or system of record.
- No **fair-value determination** or hierarchy-classification decision issued as final —
  surface the inconsistency; the classification decision is the reviewer's / committee's.
- No **threshold tuning to a desk** to make a specific mark pass; use only the versioned
  config.
- No **personalized investment advice** or price target presented as a review conclusion.
- No **opaque scoring** presented as decisive; checks are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥ 1 cited evidence row (with a non-empty citation).
- No sign-off / approval / posting language (regex screen: "valuation is approved",
  "approve the override", "signed off", "post the mark to the ledger", "book the value",
  "the mark is correct/accurate/fair", "no further review is required", etc.).
- `suggested_disposition` equals the deterministic mapping from the fired findings
  (any high-severity finding, or ≥ `escalate_finding_count`, → Escalate).
- Standing disclaimer present: "Valuation review evidence only; not a valuation sign-off,
  override approval, or fair-value determination. No value has been posted or approved."
- `review_considerations` included when any finding fired.

## Conduct / independence

- Preserve **independence**: do not adopt the desk/trader mark as the answer; the independent
  price and the valuation policy are the authorities (see `source-map.md`).
- Describe adjustments, overrides, and variances **factually**; do not impute intent (e.g.
  "the desk mismarked to hit P&L") — that is an investigation conclusion, not a review.

## Data classification, privacy, records

- **Confidential (financial records).** May include position-level and issuer-confidential
  data; minimize to what evidences a fired finding.
- Retain the review + citations + `config_version` per records policy; log the read and any
  `external-delivery` approval.

## Reproducibility

`review_id` binds the output to the exact valuation record, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the findings and disposition.
