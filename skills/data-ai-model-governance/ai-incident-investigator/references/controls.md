# Controls — ai-incident-investigator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis (every disposition is a *recommendation* surfaced for human adjudication).
- **Human approval:** `required` — for incident closure, root-cause determination, model
  exoneration/redeployment, remediation acceptance, and any regulatory/breach notification.

## Prohibited (fail closed)

- **Incident closure** or **case resolution** of any kind.
- **Root-cause determination** — the skill advances *hypotheses* only.
- **Redeployment / model exoneration** or any "safe to deploy / cleared" sign-off.
- **Regulatory or breach notification** drafting, sending, or filing.
- **Containment actions** (isolate, disable, roll back) — the skill *refers* to IR/DLP.
- **Any system-of-record write** or acceptance of a routing/remediation decision.

## Case states (this skill may set only these — all recommendations)

`reported` → `needs-evidence` | `recommend-containment-referral` |
`recommend-escalate-for-adjudication` | `recommend-remediation-owner`. It may **not** set
`closed`, `resolved`, `determined`, `notified`, or `redeployed`.

## Required output screens (`scripts/validate_output.py`)

- Durable `case_id` (`AIINC-*`) on every record.
- Every chronology entry carries a citation; the evidence bundle carries citations; a bundle
  with uncited evidence fails closed.
- Only recommendation dispositions appear (no closure/determination/filing state).
- `severity_band` equals the deterministic score + escalation-class floor.
- No closure, determination, filing/notification, or redeployment-authorization language
  (regex screens over the records + narrative).
- Standing note present.

## Segregation of duties

Detection/triage, investigation (this skill), remediation ownership, and adjudication/closure
are distinct roles. The same person/skill must not both investigate and close or determine.

## Data classification, privacy, records

- **Confidential.** Include only aggregate affected-population counts; never embed customer
  identities or the raw sensitive content that caused the incident.
- Preserve the evidence bundle, citations, and config versions per records policy and any
  litigation/regulatory hold. Log investigator identity on every read and case artifact.
- Treat agent/tool logs and eval runs as chain-of-custody evidence.
