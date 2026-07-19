# Controls — data-quality-issue-investigator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis (a remediation, incident escalation, or closure is a *proposed* action recorded
  via the approval broker for a human owner).
- **Human approval:** `required` — for every disposition beyond a recommendation: confirming
  a root cause, remediating, waiving, closing, or writing any system of record.

## Prohibited (fail closed)

- **Case closure / resolution**, **root-cause confirmation**, **marking data remediated**,
  **waiving** a defect, or **filing** any report/attestation.
- **Autonomous determination** of severity as final (severity is a *recommendation* tied to
  the versioned config).
- **Auto-merge / auto-close** of issues or duplicate cases.
- **Down-ranking** a material/regulated-impact defect below incident escalation.

## Case states (this skill may set only these)

`new` → `needs-data` | `possible-duplicate` (linked) | `recommend-remediation` |
`recommend-upstream-trace` | `recommend-incident-escalation`. It may **not** set `resolved`,
`closed`, `remediated`, `root-cause-confirmed`, `waived`, or `no-issue`.

## Required output screens (`scripts/validate_output.py`)

- Durable `case_id` present on every record.
- Only recommendation dispositions appear (no closure/determination/remediation states).
- Every evidence bundle and every chronology event is cited; bundles carry their `case_id`.
- Severity band equals the deterministic mapping, using the same thresholds the engine used
  — the output's versioned `severity_config` if present, the documented defaults otherwise
  (regulatory-report override to Critical). A configured threshold ties out against itself,
  never against a hardcoded default.
- `possible-duplicate` carries a linked parent case; `needs-data` lists what is missing.
- No closure/determination/filing language (regex: "case closed", "resolved", "remediated",
  "root cause confirmed", "determination", "waiver", "signed off", "no further action",
  "data is now clean", "filed the report/attestation").
- Standing note present.

## Segregation of duties

Investigation entitlements are distinct from remediation and from issue closure. The same
person/skill must not both investigate and close/remediate the substantive issue. Detection
(monitoring) that populates the queue is a separate upstream activity.

## Data classification, privacy, records

- **Confidential.** Data-quality metadata may reference datasets/fields holding customer
  NPI/PII; operate on profiling counts and record keys, not raw record contents.
- Mask any identifier surfaced in output to what evidences the defect.
- Retain investigation records, evidence bundles, and citations with the severity-config
  version per governance recordkeeping; log analyst identity on every read/recommendation.
