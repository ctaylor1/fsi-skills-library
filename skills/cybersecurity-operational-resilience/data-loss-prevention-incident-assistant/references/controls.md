# Controls — data-loss-prevention-incident-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The package is *enrichment + classification + an exposure estimate
  with evidence and a recommendation* for a human privacy/incident-response reviewer.
- **Human approval:** `required` — before any breach determination, incident disposition/closure,
  notification decision, containment or response action, or system-of-record write. Assembling
  the draft is not itself an approval.

## Prohibited (fail closed)

- **Breach determination** — concluding, communicating, or recording that a reportable data
  breach has occurred (a privacy/legal decision).
- **Notification decision or issuance** — deciding a notification obligation applies, or
  notifying a regulator, supervisory authority, customer, or data subject.
- **Incident disposition / closure** (confirmed-exfiltration or benign verdict) or communicating one.
- **Containment / response actions**: blocking or quarantining a transfer/upload/email, revoking
  access, disabling/locking an account, blocking a destination/domain, deleting/recalling/wiping
  data or messages, credential/token rotation.
- **Suppression** outside `SUP-DUP-01`, `SUP-SANCTIONED-01`, `SUP-FP-PATTERN-01`.
- **Writing a system of record** (DLP console / case management / ticketing) or
  **sending/submitting/filing** the package or any notification.
- **Identity/access, cloud-posture, third-party, or incident-command conclusions** — route to the
  specialist / IR / privacy-legal owner.
- **Auto-merge / auto-close** of events or cases; a duplicate is **linked** for human review.
- **Evidence spoliation** — the skill records references only; it acquires, alters, and removes nothing.

## Package states (this skill may set only these)

`blocked` (hard boundary — an `active_exfiltration` indicator) | `needs-data` (any unresolved
enrichment/classification gap) | `ready-for-review` (complete, no hard boundary). It may **not**
set `closed`, `contained`, `remediated`, `resolved`, `breach-confirmed`, `notified`, or any
decision/closure state.

Per-event dispositions (allowed): `prepared-for-review` | `approved-suppressed` (rule-bound) |
`needs-data` | `correlated-duplicate` (linked). Never `closed`, `benign`, `confirmed-breach`,
`contained`, or `no-action`.

## Required output screens (`../scripts/validate_output.py`)

- `package_status` is one of the three allowed draft states.
- **Template fidelity:** all required sections present (see
  [../assets/output-template.md](../assets/output-template.md)).
- **No unsupported claims:** every `present` evidence section (`event_enrichment`,
  `data_classification`, `exposure_assessment`, `evidence_preservation`) carries citations.
- Only approved suppression rule ids appear; each suppression cites its evidence.
- Escalated events carry a cited assessment-context bundle; `severity_band` equals the
  deterministic mapping (+ active-exfiltration override).
- **Required approvals recorded:** the ledger covers every required role; any `obtained` entry
  names an approver **and** date (no fabricated sign-off).
- **Hard-boundary consistency:** an `active_exfiltration` indicator forces `package_status=blocked`.
- **Language screens:** no breach-determination/closure language, no containment/response
  language, no filing / system-of-record-write language, no send/submit language.
- **Standing note present** (draft-only / no-breach-determination limitation).

## Segregation of duties

Assessment-packaging entitlements are distinct from breach determination, incident command,
notification, and any containment/system-of-record write. The same person/skill must not both
assemble the package and adjudicate or action the incident.

## Data classification, privacy, records

- **Confidential (security-sensitive).** The package concerns potential loss of regulated data;
  restrict distribution to the DLP/privacy/IR workflow on a need-to-know basis.
- Mask actor identifiers, asset names, and destinations to what the event evidences
  (`identity_ref`, `asset_ref`, `dest_ref` are masked); **do not** reproduce the exfiltrated data
  content — reference it by classification, type, and count only.
- Record evidence references and legal-hold flags for the human owner; preserve chain-of-custody
  by recording references, never by acquiring or altering the underlying data.
- Retain the package, citations, and config/template versions per security-records and privacy
  recordkeeping policy; log the analyst identity on every read and every package assembly.
