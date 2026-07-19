# Controls — operational-risk-event-analyzer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — mandatory human adjudication before any regulated decision,
  escalation, filing, register update, posting, attestation, case closure, or system write.

## Prohibited (fail closed)

- No **risk determination**: do not confirm/finalize a loss, **accept residual risk**, or make a
  "final determination".
- No **case/event closure** and no suppression of the event outside approved deterministic logic.
- No **filing or submission**: operational-risk regulatory report, SAR, or any regulator
  submission. Raise a reporting **candidate** flag; a human decides and files.
- No **system-of-record write**: risk-register update, loss-journal posting, control
  attestation, or GL write.
- No **threshold tuning per event**; use only the versioned ERM config.
- No **individual blame or intent** language; describe control failures factually.

## Required output screens (`scripts/validate_output.py`)

- Impact arithmetic ties out: `net_loss = max(gross_loss − recoveries, 0)`,
  `total_impact = net_loss + indirect_costs`.
- `severity_band` equals the deterministic mapping from banding amount + thresholds +
  escalation flags (see [domain-rules.md](domain-rules.md)).
- Escalation flags do not **under-flag**: banding amount ≥ reporting/board threshold implies the
  corresponding candidate is set.
- Every finding has ≥ 1 cited evidence row.
- `requires_human_adjudication` is present and **true**.
- No decision/closure/filing/posting language (regex screen: "case closed", "we have filed",
  "filed the regulatory report", "posted to the general ledger", "final determination",
  "risk accepted", "write-off approved", "loss confirmed and closed", etc.).
- Standing disclaimer present: "Analysis and recommendations only; not a risk decision or
  regulatory filing. … No case action has been taken."

## Fairness / conduct

- Reference roles and records, not individual identities, where a finding does not require the
  identity. Do not use protected-class attributes.
- Conduct-related causes route to the accountable manager for handling; the skill does not reach
  a conduct conclusion.

## Data classification, privacy, records

- **Confidential.** Minimize personal data about staff/customers named in incident records.
- Retain analysis + citations + `config_version` per records policy; log read + adjudication.

## Reproducibility

`analysis_id` binds the output to the exact event record, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the classification, impact, severity, and
escalation candidates.
