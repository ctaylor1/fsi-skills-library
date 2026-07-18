# Adjacent-Skill Handoffs — loan-affordability-precheck

This skill produces an **indicative affordability estimate** (`precheck_id`) with assumptions and
stress cases, then stops. It does not verify income, decide credit, package the application, or draft
an adverse-action notice.

## Upstream (may feed this skill's inputs)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `bank-statement-analyzer` | Income, recurring obligations, cash-flow from statements | Income/obligation figures (cited) |
| `financial-spreading-assistant` | Spread borrower financials/tax returns (commercial) | Standardized income/debt lines |
| `cashflow-forecaster` | Forward cash-flow view for context | Base/downside cash-flow figures |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `credit-application-packager` | The applicant wants to proceed and the file must be assembled for submission | `precheck_id` + disclosed inputs |
| `loan-package-completeness-checker` | Verify the assembled underwriting/closing package | Application package |
| `credit-memo-drafter` | Commercial credit narrative from approved spreads | Spread + precheck context |
| **Human underwriter / loan-origination system** | Any actual credit decision, adverse-action notice, commitment, or system-of-record write | Full verified file (not just the precheck) |

## Do not route here (out of scope)

- **Statement extraction only** (no affordability question) → `bank-statement-analyzer`.
- **Commercial financial spreading** → `financial-spreading-assistant`.
- **Personalized investment/retirement modeling** → `retirement-income-scenario-modeler`.
- **The credit decision, adverse-action notice, or eligibility determination** → human underwriting;
  no skill in this library makes or communicates a binding lending decision.

## Duplicate-execution prevention

- This skill computes and evidences an **indicative estimate only**; it must not record a decision,
  send an applicant-facing decision, or write the loan-origination system — those belong to the human
  underwriter and downstream skills.
- Downstream skills reuse the `precheck_id` context rather than re-deriving affordability, and operate
  on **verified** data (the precheck uses disclosed figures).
