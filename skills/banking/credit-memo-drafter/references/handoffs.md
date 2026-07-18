# Adjacent-Skill Handoffs — credit-memo-drafter

Drafting a credit memorandum is a distinct control activity from spreading, package
certification, covenant monitoring, and — above all — the underwriting **decision**. This
skill assembles decision-support and hands off; it never decides.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `financial-spreading-assistant` | The approved financial spread (CFADS, debt service, EBITDA, ratios) | Spread reference + version |
| `bank-statement-analyzer` | Statement-level income/obligation/anomaly evidence | Source-linked analysis |
| `cashflow-forecaster` | Base/upside/downside cash-flow context for repayment | Forecast with drivers |
| `credit-application-packager` | The organized, source-linked credit package | Package + open items |

## Downstream (this skill hands off to)

| Downstream skill / party | When | Handoff artifact |
| ------------------------ | ---- | ---------------- |
| `loan-package-completeness-checker` | Certify the underwriting/closing package before human sign-off | `memo_id` draft + package |
| `covenant-compliance-monitor` | Track covenants over the life of the facility (post-booking) | Covenant definitions + citations |
| `credit-risk-portfolio-analyzer` | Assess portfolio/concentration impact of the exposure | Facility + risk-grade evidence |
| **Human underwriter / credit officer / credit committee** | The credit **decision**, pricing, exception disposition, and booking | `memo_id` draft with pending approvals |

There is **no skill** for the credit decision itself; it is a human adjudication. The memo
routes to the appropriate approver role via the approval broker as a *proposal*.

## Duplicate-execution prevention

- This skill **does not** re-spread financials, certify package completeness, monitor
  covenants, or make/record the credit decision — those belong upstream, downstream, or with a
  human approver.
- The underwriter consumes the `memo_id` draft rather than re-drafting it.
- Exceptions are documented with mitigants for the approver to dispose of; the draft never
  grants or waives them.
