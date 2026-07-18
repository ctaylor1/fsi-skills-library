# Controls — transaction-reconciliation-helper

- **Risk tier:** R2 — analytical / reconciliation. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the pack or any proposed entry
  is delivered externally or written to a system of record (the ledger). Internal analytical
  use may be reviewer-sampled.

## Prohibited (fail closed)

- No **posting, booking, or finalizing** of any entry, journal, or correction; no write to
  the ledger / GL / system of record. The skill emits **proposed** entries only.
- No **closing or suppressing** a break, and no claim that a reconciliation is "final".
- No **resolution of settlement-file / cash-ledger breaks** — those route to
  `settlement-break-reconciler`; the helper must not attach a proposed ledger entry to a
  routed settlement break.
- No **fabricated matches** — a break is not "resolved" by assuming a missing source exists.
- No **tolerance tuning to force a tie-out**; tolerances come from the versioned config.

## Required output screens (`scripts/validate_output.py`)

- **Break taxonomy:** every break/routed break has a `break_type` from the documented set
  (`missing_record, unmatched, amount_mismatch, duplicate, status_mismatch,
  currency_mismatch, timing_difference, fee_variance`).
- **Lineage:** every break has ≥1 evidence row and each row carries a citation.
- **Tie-out (deterministic recomputation):**
  `target_total == source_totals[target_source]`,
  `residual_before == target_total − ledger_total`,
  `net_proposed == Σ(ledger_delta of proposed ledger_adjustments)`,
  `residual_after == residual_before − net_proposed`.
- **Routing:** routed breaks target `settlement-break-reconciler` and carry **no** proposed
  ledger entry.
- **Proposed-only:** every proposed entry has `status: "proposed"`; no posting/finalization
  language anywhere in the pack (regex screen: "posted the journal", "booked to the general
  ledger", "ledger has been updated", "entry booked", "approved and posted", etc.).
- **Standing disclaimer** present: "Proposed entries only; not posted to any system of
  record. Human approval and posting required."

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Mask PAN/account numbers to
  last 4; never emit full card numbers. Minimize record fields to what evidences a break.
- Retain the reconciliation + citations + `config_version` per records policy; log the read
  and any external-delivery approval.

## Reproducibility

`recon_id` binds the output to the exact record set, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the matches, breaks, proposed entries,
and tie-out totals.
