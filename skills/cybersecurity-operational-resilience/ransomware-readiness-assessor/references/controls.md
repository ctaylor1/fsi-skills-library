# Controls — ransomware-readiness-assessor

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human control owner (CISO office / operational resilience)
  must adjudicate every finding and approve every staged remediation before any change,
  readiness attestation, risk acceptance, regulatory filing, or system-of-record write occurs.
  The skill produces evidence and staged candidates only.

## Prohibited (fail closed)

- No **readiness decision or attestation**: never certify/attest that a service or the
  organization is "ransomware-ready", never sign a readiness sign-off, and never state that
  readiness "is approved/assured".
- No **risk acceptance**: never accept or formally accept a gap's residual risk — risk
  acceptance is a governance decision for an accountable owner.
- No **execution**: never remediate, apply a fix, enforce MFA, re-segment a network, make a
  backup immutable, or otherwise change a control. Staged remediations are **candidates**
  (`status: staged_for_approval`), not writes.
- No **filing or reporting to a regulator**: never file/submit a readiness or incident report.
  Regulatory resilience reporting is a separate workflow (`operational-resilience-reporter`).
- No **closure**: never close the assessment/case or suppress a finding outside the documented
  deterministic logic.
- No **threshold tuning to the assessed entity**: use only the versioned config (intervals,
  coverage/MFA thresholds, relevant exercise types).
- No **opaque scoring** presented as decisive; findings are explainable, rule-based, and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥ 1 cited evidence row.
- `suggested_priority` equals the deterministic mapping from `fired_findings`.
- No decision / attestation / risk-acceptance / remediation-execution / filing / closure
  language in the narrative, notes, or finding reasons (regex screen: "certify readiness",
  "is ransomware-ready", "risk is accepted", "we remediated", "backups have been made
  immutable", "filed the report", "assessment is closed", etc.).
- Every staged remediation is a candidate (`status` ∈ {staged_for_approval, pending_approval,
  recommended}) tied to a **fired** finding — an executed/completed status fails closed.
- Standing disclaimer present: "Ransomware-readiness assessment: evidence and staged remediation
  recommendations only; not a readiness decision or attestation. No remediation has been executed
  and no assessment has been filed or closed."
- `context_prompts` included when any finding fired.

## Conduct

- The skill supports the readiness control; it does not *own* the readiness decision. Flag gaps
  with evidence and stage candidates for the control owner — never choose to accept a risk or
  declare a service ready.
- Describe a gap as a **control exception with evidence**, never as an accusation of negligence
  or a prediction that a ransomware event will occur.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Control-posture and critical-service data is sensitive;
  minimize output to the services/controls that evidence a fired gap. Do not disclose exploitable
  detail (exact host inventories, credentials, live configuration) beyond what evidences the gap.
- Retain the assessment + citations + `config_version` per records policy; log the read and any
  control-owner approval of staged remediations.

## Reproducibility

`readiness_id` binds the output to the exact extract, `as_of`, and **config version**; re-running
with the same inputs and config reproduces the findings, staged candidates, and priority.
