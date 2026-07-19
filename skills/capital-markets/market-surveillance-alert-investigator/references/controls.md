# Controls — market-surveillance-alert-investigator

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis (any case-state transition is a *proposed* action via the approval broker).
- **Human approval:** `required` — a qualified supervisor / compliance officer must
  adjudicate **every** disposition. This skill produces cited evidence and a
  **recommendation only**; it never makes the call.

## Prohibited (fail closed)

- **Autonomous case closure** or setting a system-of-record disposition (`closed`,
  `no-action`, `cleared`).
- **Market-abuse determination** — asserting that spoofing, layering, wash trading, marking
  the close, insider dealing, or collusion *occurred*. The skill reports **indicators**, not
  findings.
- **Regulatory filing** — drafting/filing a STOR, SAR, or any regulator submission, or
  stating that one was filed.
- **Exonerating** a trader/account, or **disciplinary** conclusions.
- **Investigating an un-escalated alert** — no triage provenance ⇒ fail closed and route to
  `surveillance-alert-triager`.

## Disposition recommendations (this skill may emit only these)

`recommend-refer-regulatory-consideration` | `recommend-escalate-to-compliance-review` |
`recommend-close-no-further-action` | `needs-data` | `possible-duplicate`.

Every one is a **recommendation** for human adjudication. The skill may **not** emit
`closed`, `cleared`, `no-action`, `confirmed`, or any determination/filing state.

## Required output screens (`scripts/validate_output.py`)

- **Durable case_id** present on every case, form `MKT-SURV-<alert_id>` (idempotent).
- **Escalation provenance** present (`triage_case_id` + `escalated_by`).
- Disposition ∈ the allowed recommendation set (no closure/determination/filing states).
- **Every evidence item cited** — each chronology event, indicator, and party carries a
  citation; the bundle exposes a non-empty citation list.
- **Disposition consistency** — strength-based recommendations tie out to
  `evidence_strength_score` and the documented bands.
- **No closure/determination/filing language** (regex screen over records + narrative):
  e.g. "case closed", "confirmed market abuse", "determination of manipulation", "filed a
  STOR", "exonerated", "no further action taken". Fail closed on any hit.
- **Standing note** present and unaltered.

A NON-COMPLIANT fixture (`evals/files/evidence_bad.json`) with closure/determination/filing
language and a disallowed disposition **must fail closed** (`expect_exit 1`).

## Segregation of duties

Triage, investigation, and adjudication are **distinct control activities** with distinct
entitlements. The same person/skill must not both triage and investigate, nor both
investigate and adjudicate/close. Investigation consumes a triage escalation and hands a
disposition **recommendation** to an authorized adjudicator.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII + MNPI).** Communications content and identities
  are sensitive; mask account/party identifiers to what the evidence requires.
- **Information barriers:** surface MNPI/insider signals as *indicators for review*; do not
  broadcast MNPI beyond the authorized surveillance/compliance channel.
- Retain the evidence bundle, indicator values, thresholds/config version, and citations per
  the firm's surveillance recordkeeping obligations; log analyst identity on every read and
  on the recommendation.
