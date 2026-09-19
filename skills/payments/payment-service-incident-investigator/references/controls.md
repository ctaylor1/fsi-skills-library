# Controls — payment-service-incident-investigator

- **Risk tier:** R2 — analytical/investigation support. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — external delivery requires human sign-off; no
  configuration is ever changed by this skill.

## Prohibited (fail closed)
- No **config change**, **key rotation**, **rule disable**, or **fix deployment**.
- No **auto-remediation** of any kind.
- No **guessed classification** for an unknown code (use `unclassified`).
- No **cardholder data (PAN) in the output** — redaction is mandatory and screened.

## Required output screen (`scripts/validate_output.py`)
- **PAN-leakage screen**: no 13–19 digit sequence survives anywhere in the output.
- No remediation/config-change language (regex: changed the config/deployed the fix/disabled the
  rule/rotated the key/we fixed/applied the patch).
- Every classified entry has a category (including `unclassified`).
- Standing disclaimer present.

## Segregation of duties
The diagnostic engineer investigating is not authorized by this skill to change production; the
pack supports, never replaces, the change process.

## Data classification, privacy, records
- **Highly Confidential (cardholder data / PCI + NPI/PII).** Redact PAN everywhere.
- Retain the redacted pack + citations + taxonomy version; log read + external-delivery approval.

## Reproducibility
`diagnostic_id` binds output to the exact log window and taxonomy version; computation is
deterministic and stdlib-only.

## Phase 1 implementation boundary

Phase 1 boundary: the calculator categorizes supplied log entries; no success denominator, retry-chain/lifecycle reconstruction or causal incident analysis is implemented. Counts are not an authorization failure rate and most-common error is not proven root cause. A service-incident investigator is later-phase work.

Phase 3 incident mode is R3 decision support with mandatory human adjudication. No incident closure, replay, posting, configuration change or recovery execution is authorized. Use redacted/opaque evidence inputs.
