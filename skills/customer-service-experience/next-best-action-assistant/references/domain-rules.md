# Domain Rules — next-best-action-assistant

Orientation references: the firm's customer-treatment / fair-treatment standard, marketing
consent and do-not-contact policy, vulnerable-customer policy, and the product governance
(suitability of offers) standard. The firm's **approved action catalog** and **eligibility
rules** are versioned contracts and take precedence over anything inferred from a transcript.

## The action catalog is the allow-list

Only actions present in the approved catalog may be recommended. Each catalog entry carries:
`type` (education | service | retention | cross-sell | referral | advice), `eligibility`,
`requires_consent` (channel or null), `requires_specialist`, `binding_category` (or null),
`required_disclosures`, `source_refs`, and `benefit_score`. An action not in the catalog, or
lacking a citation, is **unsupported** and must not appear.

## Eligibility evaluation (deterministic, documented)

An action is eligible only if **all** hold (see `scripts/calculate_or_transform.py`):

| Rule | Meaning |
| ---- | ------- |
| `products_any` | If non-empty, the customer must hold at least one listed product. |
| `products_none` | The customer must not already hold any listed product. |
| `min_tenure_months` | Customer tenure must meet the minimum. |
| `requires_signals` | All listed context signals must be present and truthy. |
| `excluded_segments` | The customer's segment must not be excluded. |

## Gating (applied after eligibility, in order)

1. **Prohibited binding decision** — any `binding_category` in {credit_decision,
   claim_decision, investment_advice, suitability_determination} is **never** recommended; it
   is routed to a licensed specialist. (Checked first, before eligibility, so a binding entry
   can never surface.)
2. **Vulnerability** — if the customer has a vulnerability flag, retention and cross-sell
   actions are **suppressed** and routed to `vulnerable-customer-support-assistant`.
3. **Consent / do-not-contact** — an action with `requires_consent = <channel>` is excluded
   unless the customer granted that channel's consent and has no do-not-contact flag.

## Ranking

Eligible actions are ranked by `score = benefit_score + (number of matched required signals)`,
descending, with `action_id` as a deterministic tie-break. Ranking orders a human's options;
it is not an approval or a decision.

## Hard boundaries (fail closed)

- No **binding decision** (credit, claims, investment/suitability) — refer, never decide.
- No **unsupported/unapproved claims** — every action is catalog-sourced and cited; no
  guarantees, "pre-approved", "best investment", or advice language.
- No **sending/submitting/posting** — draft-only; external delivery needs recorded approval.
- No **outbound action** without matching channel consent (and no do-not-contact).
- No **retention/cross-sell** to a vulnerability-flagged customer.

## Required package contents

Customer context snapshot (cited); ranked recommendations (each cited, with rationale,
eligibility basis, and required disclosures); consent & eligibility checks; excluded / routed
items with reasons; aggregated disclosures; recorded approvals (pending); sources; standing
note. See `assets/output-template.md`.
