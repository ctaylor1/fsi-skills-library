# Controls — third-party-cyber-risk-reviewer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human risk owner must adjudicate before any supplier
  decision, risk acceptance, onboarding, exception, filing, attestation, or GRC/TPRM system
  write. This skill produces findings + cited evidence + a suggested tier only.

## Prohibited (fail closed)

- No **supplier decision**: never approve, reject, onboard, clear, or risk-accept a supplier
  or engagement.
- No **closure or sign-off**: never close the assessment/case, sign off, waive a finding, or
  grant an exception.
- No **filing / attestation / final determination**: never file, attest, or state a final
  approval/determination.
- No **system-of-record write**: no GRC/TPRM register update, contract execution/termination,
  or exception-log entry.
- No **threshold tuning to a single supplier** to reach a desired tier; use only the
  versioned config and record `config_version`.
- No **opaque scoring** presented as decisive; findings are explainable and individually
  evidenced.

## Required output screens (`scripts/validate_output.py`)

This is the R3 prohibited-decision screen; it **fails closed** on any miss:

- Every fired finding has ≥1 cited evidence row.
- `suggested_residual_tier` equals the deterministic mapping from findings + engagement and
  is one of Low/Moderate/High/Critical.
- No supplier-decision / risk-acceptance / closure / sign-off / filing / termination language
  (regex screen: "supplier is approved", "we accept the residual risk", "signed off",
  "closed the assessment", "filed the attestation", "contract is executed", etc.).
- Standing disclaimer present: "Findings and evidence only; not a supplier approval, risk
  acceptance, or onboarding decision. A human risk owner must adjudicate. No system of record
  has been updated."
- Considerations / compensating-control notes included when any finding fired.

## Fairness / conduct

- Assess the supplier's security posture on evidence; do not infer beyond the cited data.
- Describe gaps factually; where an internal record contradicts an attestation, cite both.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Supplier security posture is sensitive; minimize to
  what evidences a fired finding. De-identify supplier identifiers in shared artifacts where
  the deployment requires it.
- Retain the review + citations + `config_version` per records policy; log the read and the
  human adjudication decision (made outside this skill).

## Reproducibility

`review_id` binds the output to the exact inputs, thresholds, and **config version**;
re-running with the same intake and config reproduces the findings and suggested tier.
