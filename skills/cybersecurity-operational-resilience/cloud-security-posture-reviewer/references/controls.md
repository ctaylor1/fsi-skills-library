# Controls — cloud-security-posture-reviewer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a cloud/platform owner, security control owner, or CISO/GRC
  delegate must adjudicate. The skill produces findings, cited evidence, and remediation
  recommendations; it decides and acts on nothing.

## Prohibited (fail closed)

- No **compliance attestation** — never state or imply that an account, environment, posture,
  or resource is secure or compliant, or that it passes an audit or a framework (PCI, SOC 2,
  FFIEC, NIST). Attribute any attestation to the human control owner / GRC.
- No **risk acceptance** — never accept a risk or state that a risk is accepted; surface the
  evidence and route the acceptance decision to the owner.
- No **finding closure or suppression** — never close, suppress, dismiss, waive, or mark a
  finding resolved/accepted/false-positive in a system of record.
- No **exception or waiver** — never grant, approve, or file an exception, waiver, or POA&M.
- No **remediation execution or configuration write** — never apply/deploy a fix, change a
  security group, modify an IAM/bucket policy, rotate keys, or enable/disable a setting. The
  skill recommends remediation; a human applies it.
- No **system-of-record write** — the skill is read-only.

## Required output screens (`scripts/validate_output.py`)

- Every finding has >= 1 cited evidence row (resource record + config rule), non-empty citation.
- No attestation / risk-acceptance / closure / exception / remediation-execution language
  (regex screen: "environment is compliant/secure", "attested SOC 2 compliance", "accept the
  risk", "close/suppress/waive the finding", "grant an exception", "we have remediated", "apply
  the fix now", "changed the security group", etc.). The standing disclaimer text is stripped
  before scanning so its negations do not self-trigger the screen.
- `posture_disposition` equals the deterministic mapping from finding severities (any critical →
  remediate_now; any high → remediation_required; any medium/low → review_recommended; else
  posture_acceptable).
- Standing disclaimer present: "Posture findings and remediation evidence only; not a compliance
  attestation or risk-acceptance decision. No finding closure, suppression, waiver, or risk
  acceptance has been made, no exception has been granted, and no cloud configuration change or
  remediation has been applied."
- `reviewer_considerations` included whenever any finding is present.

## Fairness / conduct

- Describe misconfigurations factually against the resource and the config rule; do not
  attribute blame to a named individual or team.
- Never include live secrets, keys, tokens, or credential material in a finding or the pack.

## Data classification, privacy, records

- **Confidential (security-sensitive).** A posture export enumerates exploitable weaknesses;
  minimize to what evidences a finding, mask account identifiers where surfaced, and never route
  the export to a destination the user did not specify.
- Retain the review + citations + `config_version` per records policy; log the read and any
  approval to write the review into a case.

## Reproducibility

`review_id` binds the output to the exact posture export, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the findings and the disposition.
