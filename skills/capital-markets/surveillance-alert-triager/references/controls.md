# Controls — surveillance-alert-triager

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only
  analysis (escalation is a *proposed* state transition via the approval broker).
- **Human approval:** `required` — for every escalation disposition, any case closure, any
  market-abuse determination, and any regulatory filing. Approved suppression is a bounded,
  logged, reviewer-sampled action.

## Prohibited (fail closed)

- **Case closure**, **market-abuse / manipulation / insider-trading determination**,
  **exoneration**, or **regulatory filing** (STR/SAR/regulator report).
- **Suppression** outside `SUP-DUP-01`, `SUP-WL-KNOWN`, `SUP-CALIB-01`.
- **Scenario/typology determination** (hints for routing only; naming a scenario is not
  concluding it).
- **Auto-merge / auto-close** of alerts or entities.

## Case states (this skill may set only these)

`new` → `needs-data` | `possible-duplicate` (linked) | `approved-suppressed` (rule-bound) |
`escalate-to-investigation`. It may **not** set `closed`, `cleared`, `determined`, `filed`,
or `no-action`.

## Required output screens (`scripts/validate_output.py`)

- Every record carries a durable `case_id` (`SURV-*`).
- Only approved suppression rule IDs appear; each suppression cites its evidence.
- Every escalation bundle is cited and carries a chronology; **every chronology event cites**.
- Disposition is a RECOMMENDATION only; no closure/determination/filing states.
- No closure/determination/filing language (regex: "close the case", "cleared", "no market
  abuse found", "not market abuse", "we determine/conclude/find", "final disposition",
  "confirmed spoofing/manipulation", "file the str/sar", "no further action").
- `priority_band` equals the deterministic mapping (restricted-list proximity overrides P1).
- Standing note present: "First-line triage only; no case has been closed, no determination
  of market abuse has been made, and nothing has been filed."

## Segregation of duties

Triage entitlements are distinct from investigation and from any regulatory filing. The same
person/skill must not both triage-suppress and adjudicate/close the substantive case.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Surveillance evidence may include MNPI and
  personal communications; handle on a need-to-know basis and do not tip subjects.
- Mask account/desk/party identifiers to what evidences the alert.
- Retain triage records, suppression logs, and citations with rule/config versions per the
  firm's surveillance recordkeeping standard; log analyst identity on every read,
  suppression, and escalation.
