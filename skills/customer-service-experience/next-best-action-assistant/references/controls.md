# Controls — next-best-action-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — a servicing supervisor / QA reviewer must approve
  before any recommendation is delivered externally or written to a system of record; internal
  drafting is reviewer-sampled. A referral is only acted on after licensed-specialist sign-off.

## Prohibited (fail closed)

- **Binding decisions**: credit approval/adverse action, claim coverage/denial, investment
  advice, or suitability determinations. These are **excluded** from recommendations and
  **routed** to a licensed specialist. NBA refers; it never decides.
- **Unsupported / unapproved claims**: guarantees of return/approval/rate, "pre-approved",
  "best investment", "risk-free", "you will be approved", "we recommend you buy/sell". Every
  recommended action must come from the approved catalog and carry a citation.
- **Sending / submitting / posting**: the skill drafts only. It never sends a message, submits
  a form, executes an action, or updates a system of record.
- **Recommending actions not in the approved catalog** (the catalog is the allow-list).
- **Outbound actions without matching channel consent**, or when do-not-contact is set.
- **Retention / cross-sell to a customer with a vulnerability flag** (suppress and route to
  specialist support).

## Package states (this skill may set only these)

`draft` (ranked recommendations, approvals `pending`). It may **not** set `delivered`, `sent`,
`approved`, or write any account/CRM state. `external_delivery` stays `false` until a human
records approval (`status: approved`) in a downstream, entitled step.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (template fidelity).
- Every recommendation carries a citation; no recommendation is a prohibited binding decision.
- No guarantee/advice/approval claim language; no send/submit/executed/system-of-record
  language (draft-only).
- Approvals recorded: required-approver list present; `external_delivery` not true unless
  `status` is `approved`.
- Standing note present ("Draft recommendations only… no… binding credit, claims, or
  investment decision…").

## Segregation of duties

Drafting next-best-actions is distinct from approving/delivering them and from any licensed
decision (lending, claims, investment suitability). The agent who drafts must not self-approve
external delivery, and must not substitute NBA output for a licensed specialist's decision.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask customer/account identifiers to what the
  package needs; do not export raw PII into rationale text.
- Consent, do-not-contact, and vulnerability flags are honored on every package.
- Retain the draft package, its `config_version`, citations, and the recorded approvals; log
  the agent identity on every read and every package produced.
