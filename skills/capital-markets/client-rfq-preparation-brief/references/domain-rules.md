# Domain Rules — client-rfq-preparation-brief

Orientation: give a sales trader the context and surfaced flags needed to respond to an RFQ
responsibly. The brief informs; it never prices, commits, or decides suitability.

## Sections assembled (deterministic)
- `instrument_summary` — type, notional, currency, side (from the RFQ).
- `client_summary` — tier, jurisdiction, relationship (from CRM).
- `suitability_review` — surfaced flags (see below), not a determination.
- `prior_activity` — recent trades/inquiries summarized.

## Suitability/eligibility flags (surfaced, never decided)
| Flag | Rule |
| ---- | ---- |
| `kyc_not_current` | `client_context.kyc_status` is not `current` |
| `restricted_product` | Instrument type appears in `client_context.restricted_products` |
| `jurisdiction_restricted` | Instrument/jurisdiction pair appears in the policy's restricted list |

A flag reports the rule and the fact; it is **not** a decision to decline or proceed.

## Completeness (deterministic)
- Each `required_section` must have its underlying data present; a missing one is a completeness
  gap.

## Disposition mapping (review-only)
- `ready-for-review` — no flags and no gaps.
- `review-required` — ≥1 flag or gap. A triage suggestion for the trader/compliance, **not** a
  suitability decision.

## Hard boundaries (fail closed)
- Never price/quote/bid/offer; never commit or execute; never determine suitability/eligibility;
  never assume eligibility for missing context.
