# Adjacent-Skill Handoffs — credit-application-packager

Packaging (this skill) is a **separate control activity** from completeness certification,
credit-memo drafting, and credit decisioning — each has different entitlements,
accountability, and downstream reliance. This skill emits a durable `package_id` and an
assembled manifest; it does not perform the checker's, drafter's, or underwriter's work.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `loan-package-completeness-checker` | Package assembled; formal pre-underwriting or closing completeness certification is needed | `package_id` + assembled manifest + open-items list |
| `credit-memo-drafter` | Package assembled and financials spread; a commercial credit memo is needed | `package_id` + source index + cited financial section |
| `covenant-compliance-monitor` | Deal has covenants requiring ongoing monitoring after booking | `package_id` + collateral/covenant references |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `financial-spreading-assistant` | Spread borrower statements/tax returns to attach as the financial component |
| `bank-statement-analyzer` | Extracted income/obligations/cash-flow evidence for the financial section |
| `customer-onboarding-document-checker` | Checked KYC/onboarding artifacts to attach as the KYC component |

The transaction/loan origination system produces the raw application and documents. This skill
is **interactive** packaging (`aws-fsi-scheduled-agent: no`); a monitor may populate a queue
but must not assemble, certify, or decide.

## Non-catalog handoffs (human / licensed)

- **Credit decision / adverse action** → the underwriter or licensed decisioner (no catalog
  skill makes a binding credit decision). For indicative-only affordability, see
  `loan-affordability-precheck` — it too avoids approval/adverse-action.
- **External delivery** of the package → a human approves and delivers via the approval
  broker; this skill never sends or submits.

## Duplicate-execution prevention

- This skill **does not** certify completeness, draft the credit memo, spread financials, or
  decide credit — those belong to the named skills or to a human.
- The completeness checker and memo drafter consume this skill's `package_id`/manifest rather
  than re-assembling.
- A borrower-identity mismatch is left `unresolved` for a human, never auto-merged here.
