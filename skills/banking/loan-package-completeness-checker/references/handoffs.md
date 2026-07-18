# Adjacent-Skill Handoffs — loan-package-completeness-checker

This skill produces a cited **completeness assessment** (`assessment_id`) and stops. It does
not decide the loan, calculate fees/APR, verify identity, waive conditions, or certify/close
the package.

## Upstream (may feed this skill)

| Upstream skill | Provides | Boundary |
| -------------- | -------- | -------- |
| `credit-application-packager` | The assembled application/underwriting package to be checked | This skill checks a finished package; it does not assemble one |
| `loan-affordability-precheck` | Affordability screen result feeding the file | Affordability is not a completeness finding here |
| `credit-memo-drafter` | The credit narrative accompanying the package | This skill checks completeness, not the credit rationale |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `fee-and-charge-reviewer` | The closing disclosure needs fee / APR / tolerance review | `assessment_id` + closing_disclosure doc |
| `kyc-customer-due-diligence-screener` | Identity / CDD documents need verification, not just presence | loan_id + identity docs |
| `beneficial-ownership-verifier` | Entity borrower beneficial-ownership confirmation is required | loan_id + entity docs |
| `covenant-compliance-monitor` | Post-closing covenant tracking once the loan is booked | loan_id + executed agreement |
| `loan-servicing-exception-resolver` | Post-booking servicing exceptions surface later | loan_id |

## Human / operations handoffs (no catalog skill)

- The **certification, clear-to-close, and any condition waiver** decision goes to the
  qualified human certifier / underwriter / closing agent — never made by this skill.
- **State-specific legal document adequacy** (beyond presence/signature/expiration) and
  novel jurisdiction requirements go to loan compliance / counsel; this skill checks against
  the configured jurisdiction checklist and flags gaps, it does not opine on legal sufficiency.

## Duplicate-execution prevention

- This skill computes and evidences **completeness findings only**; it must not reach a
  lending decision, waive a condition, or certify/close/fund the loan — those belong to the
  human certifier and the downstream systems.
- Downstream skills reuse the `assessment_id` evidence rather than re-scanning the package.
