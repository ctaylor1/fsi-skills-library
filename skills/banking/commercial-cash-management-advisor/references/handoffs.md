# Adjacent-Skill Handoffs — commercial-cash-management-advisor

This skill produces a cited **service-fit advisory** (`advisory_id`) and stops. It does not
price, decide credit, advise on investments, or enroll a service.

## Upstream (may feed this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `bank-statement-analyzer` | Extracted income, obligations, cash-flow trends, and fees from raw statements when the input is not already a structured cash profile |
| `cashflow-forecaster` | Forward base/upside/downside cash-flow view to size liquidity/buffer conversations |
| `customer-onboarding-document-checker` | Confirms onboarding documents are complete when a new relationship is being reviewed |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `fee-and-charge-reviewer` | The client wants existing account fees analyzed against disclosed terms | `advisory_id` + account list |
| `merchant-fee-optimizer` | Card-acceptance / merchant-services cost review (payments) | `advisory_id` + card volume |
| `credit-application-packager` | The overdraft/liquidity **referral** proceeds to a formal commercial-lending review | referral note + activity evidence |
| `kyc-customer-due-diligence-screener` | A new service/entity requires customer due diligence before enrollment | customer + entity context |
| `account-anomaly-screener` | The review surfaces unusual account activity needing screening | account + focal activity |

## Human / operations handoffs (no catalog skill — route in prose)

- **Pricing & product desk** — any rate/ECR/fee commitment or signed proposal. This skill
  never prices.
- **Commercial lending / underwriter** — the actual credit **decision** on a line or
  overdraft facility. `credit-application-packager` only assembles the package; the decision
  is a licensed human process.
- **Licensed investment specialist** — sweep/investment suitability and any advice on a
  specific investment vehicle. This skill never gives investment advice.
- **Treasury operations** — opening, enrolling, changing, or pricing a service in the system
  of record (an authorized action, not this skill).

## Duplicate-execution prevention

- This skill computes and evidences **service fit only**; it must not price, decide credit,
  advise on investments, or enroll a service — those belong to the human desks above.
- Downstream skills reuse the `advisory_id` evidence rather than recomputing fit.
