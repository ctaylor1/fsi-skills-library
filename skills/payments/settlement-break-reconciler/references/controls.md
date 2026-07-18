# Controls — settlement-break-reconciler

- **Risk tier:** R2 — analytical / reconciliation. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the break pack or proposed
  corrections are delivered externally (settlement/GL team, close process) or written to any
  system of record. Internal analytical use may be reviewer-sampled.
- **Data classification:** Highly Confidential (customer NPI/PII; cardholder data). Handle
  under PCI DSS scope: never emit a PAN; use scheme + masked funding references only.

## Prohibited (fail closed)

- No **posting** of any journal, adjustment, or correction; no write to the ledger, bank,
  processor, or any system of record. Corrections are **proposed only**.
- No marking a break **reconciled/cleared/closed** as a state change — the reconciliation
  reports status; a human dispositions it.
- No **executing a repair**, resubmitting a payment, or contacting the network/processor as
  an action — those are downstream, authorized steps.
- No **inventing a match**: if records do not match on the key within tolerance, classify a
  break; do not force a tie-out.
- No **tolerance tuning to make a break disappear**; tolerances come only from the versioned
  config.

## Required output screens (`scripts/validate_output.py`)

- **Tie-outs:** a `tie_out` summary with numeric per-source totals and the bank-vs-processor
  and ledger-vs-processor differences; every break `impact` is numeric.
- **Break taxonomy:** every break `break_type` is drawn from the documented taxonomy
  (domain-rules.md); no unknown types.
- **Lineage:** every break and every proposed correction cites ≥1 evidence row with a
  non-empty citation.
- **Idempotency:** `reconciliation_id` present; `break_id`s unique; `correction_id`s unique
  and each correction references exactly one existing break.
- **Proposed-only:** every correction has `status: "proposed"` and `requires_approval: true`;
  no correction carries a posted/booked/executed/applied status; the narrative contains no
  "posted the journal / applied the correction" language.
- **Consistency:** reported `total_break_impact` equals the sum of `|break impact|`.
- **Disclaimer:** standing draft-only disclaimer present.

## Data classification, privacy, records

- Mask card/account numbers (PCI): work from scheme + funding reference, never the PAN.
- Minimize data to what evidences a break. Retain the reconciliation + citations + config
  version per records policy; log the read and any external-delivery approval.

## Reproducibility / idempotency

`reconciliation_id` binds the output to the exact inputs and **config version**. Re-running
with the same inputs and config reproduces the same breaks, impacts, and `correction_id`s —
so re-running never creates duplicate proposed corrections.
