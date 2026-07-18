# Controls — due-diligence-packager

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The pack is an internal draft artifact.
- **Human approval:** `external-delivery` — a diligence lead **and** an independent quality
  reviewer must be recorded in the approvals ledger, and both must be `approved` before the
  pack is marked ready for external delivery. The send/submit itself is a human action.

## Prohibited (fail closed)

- **Sending, submitting, emailing, or delivering** the pack to any counterparty or external
  party; **filing** or writing any system of record.
- **Unsupported assertions**: any extracted data point or issue whose `source_doc` is not in
  the indexed source list. It is excluded (`needs-source`), never "cited to the data room."
- **Valuation opinions or investment recommendations** (buy/sell/hold, "should acquire",
  price targets, guaranteed returns) — these belong to the modeling skills and human deal team.
- **Personalized investment, legal, or tax advice.**
- **Inventing a downstream skill**: model handoffs may target only known modeling skills.
- **Resolving issues on the target's behalf** or marking diligence complete when workstreams
  are missing.

## Pack states (this skill may set only these)

`draft` → `needs-source` (items excluded) | `incomplete` (tool timeout / missing workstream) |
`ready-for-review`. It may **not** set `delivered`, `sent`, `filed`, `final`, or `approved`
on its own — approval and delivery are human actions recorded in the ledger.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (cover, executive_summary, source_index,
  extracted_data, issue_log, open_questions, completeness, model_handoffs, approvals,
  standing_note).
- **No unsupported claims**: `unsupported_claims` empty and every extracted-data/issue item
  resolves to a doc in `source_index`.
- **Model-handoff targets** are known modeling skills (no invented downstream skill).
- **Required approvals recorded**: `diligence_lead` and `quality_reviewer` present with a
  status; `external_delivery` may be `true` only if both are `approved`.
- **No send/submit/external-delivery language** (draft-only): regex screen for "send/submit/
  email/deliver the pack", "to the buyer/seller/counterparty".
- **No investment-recommendation / valuation-opinion / advice language.**
- Standing note present.

## Segregation of duties

Packaging entitlements are distinct from modeling, from approval, and from delivery. The same
person/skill must not both draft the pack and approve it for external delivery.

## Data classification, privacy, records

- **Highly Confidential — MNPI / client-confidential.** Apply information barriers and
  need-to-know; mask target/counterparty identifiers to what the pack requires.
- Retain the pack, source index, citations, model-handoff bundles, and approval ledger with
  document versions per the engagement records policy; log analyst identity on every read,
  draft, and approval.
