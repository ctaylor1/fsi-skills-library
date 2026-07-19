# Controls — model-inventory-maintainer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — Model Risk Governance must adjudicate before any inventory
  record is posted, any model is approved/attested/certified, any lifecycle state is
  committed, or any finding is closed.

## Prohibited (fail closed)

- No **autonomous decision**: do not approve, attest, certify, sign off, or clear a model or
  agent for production/use.
- No **system-of-record write**: do not post, update, or register the record in the inventory,
  registry, or issue tracker. The proposal is `proposed` only.
- No **case/finding closure** and no **filing** of any kind — recommendations require human
  adjudication.
- No **materiality tuning to the owner**: the tier comes from the versioned rubric applied to
  the documented factors, not from negotiation.
- No **silent conflict resolution**: reconciliation breaks are recorded and typed, never
  overwritten to force a match.

## Required output screens (`scripts/validate_output.py`)

- `status` is `proposed`; `requires_adjudication` is `true`; an adjudication owner is named.
- `computed_materiality_tier` equals the deterministic rubric — the effective thresholds the
  compute step recorded in `materiality_tie_out.config` (strict defaults when none is echoed)
  — applied to the recorded `materiality_tie_out.factors`. A configured, non-default rubric
  ties out to itself, not to the hardcoded default.
- Every finding has ≥1 cited evidence row (non-empty citation) — evidence traceability.
- Every reconciliation break is typed from the taxonomy
  (`missing_in_inventory` / `missing_in_source` / `value_mismatch` / `stale`).
- No autonomous-decision / posting / approval / attestation / closure / filing language
  (regex screen: "posted to the inventory", "approved for production", "certified",
  "attested", "signed off", "cleared for use", "closed the finding", "no adjudication
  needed", "auto-approve", etc.).
- Standing disclaimer present: "Proposed inventory changes and findings only; not an
  approval, attestation, or system-of-record update. Model Risk Governance adjudication is
  required before any change is posted."

## Fairness / conduct

- Do not up- or down-tier materiality based on who owns the model or business pressure.
- Describe gaps and breaks factually; attribute the adjudication decision to the human owner.

## Data classification, privacy, records

- **Confidential.** Minimize proprietary model detail and owner PII to what the change needs.
- Retain proposal + citations + `config_version` for reproducibility; log the read and the
  human adjudication decision (not made by the skill).

## Reproducibility

`proposal_id` binds the output to the exact inputs, source snapshots, and **config version**;
re-running with the same inputs and rubric version reproduces the tie-out, completeness,
lifecycle check, reconciliation, and findings.
