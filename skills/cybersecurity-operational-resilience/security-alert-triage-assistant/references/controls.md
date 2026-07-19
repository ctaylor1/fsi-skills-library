# Controls — security-alert-triage-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The package is *enrichment + a prioritized recommendation with
  evidence* for a human analyst.
- **Human approval:** `required` — before any alert closure, incident declaration/closure,
  containment or response action, or system-of-record write. Assembling the draft is not
  itself an approval.

## Prohibited (fail closed)

- **Alert closure / disposition** (true-positive or false-positive verdict) or communicating one.
- **Incident declaration or closure** — that is the incident-response process's decision.
- **Containment / response actions**: isolating a host, disabling/locking an account, blocking
  an IP/domain/hash, resetting or rotating credentials, killing a process/session, remediation.
- **Suppression** outside `SUP-DUP-01`, `SUP-SCANNER-01`, `SUP-MAINT-01`.
- **Writing a system of record** (SIEM/SOAR/ticketing) or **sending/submitting** the package.
- **Threat-intel disposition, vulnerability prioritization, cloud-posture confirmation, or
  identity/access review as a conclusion** — route to the specialist.
- **Auto-merge / auto-close** of alerts or cases; a duplicate is **linked** for human review.

## Package states (this skill may set only these)

`blocked` (hard boundary — active-compromise indicator) | `needs-data` (any unresolved
enrichment gap) | `ready-for-analyst` (complete, no hard boundary). It may **not** set
`closed`, `contained`, `remediated`, `resolved`, `incident-declared`, or any decision/closure
state.

Per-alert dispositions (allowed): `prepared-for-investigation` | `approved-suppressed`
(rule-bound) | `needs-data` | `correlated-duplicate` (linked). Never `closed`, `false-positive`,
`contained`, or `no-action`.

## Required output screens (`../scripts/validate_output.py`)

- `package_status` is one of the three allowed draft states.
- **Template fidelity:** all eleven required sections present (see
  [../assets/output-template.md](../assets/output-template.md)).
- **No unsupported claims:** every `present` evidence section (`alert_enrichment`,
  `asset_identity_map`, `investigation_context`) carries citations.
- Only approved suppression rule ids appear; each suppression cites its evidence.
- Escalated alerts carry a cited investigation-context bundle; `priority_band` equals the
  deterministic mapping (+ known-malicious override).
- **Required approvals recorded:** the ledger covers every required role; any `obtained` entry
  names an approver **and** date (no fabricated sign-off).
- **Hard-boundary consistency:** an active-compromise indicator forces `package_status=blocked`.
- **Language screens:** no decision/closure language, no containment/response language, no
  filing / system-of-record-write language, no send/submit language.
- **Standing note present** (draft-only / no-decision limitation).

## Segregation of duties

Triage-packaging entitlements are distinct from alert disposition, incident command, and any
containment/system-of-record write. The same person/skill must not both assemble the package
and adjudicate or action the alert.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Restrict distribution to the SOC/IR workflow.
- Mask asset names and identity identifiers to what the alert evidences (`asset_ref`,
  `identity_ref` are masked).
- Retain the package, citations, and config/template versions per security-records policy; log
  the analyst identity on every read and every package assembly.
- Do not compile personal data beyond the security-triage scope; treat alert content and
  indicators as need-to-know.
