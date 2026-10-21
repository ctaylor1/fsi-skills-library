# Independent portfolio and governance forward review

Reviewer: business/research stream, separate from the author of the eight packages. Date: 2026-09-21. This review used fresh synthetic requests designed from the documented inputs and calculators, without reading native golden fixtures. Exact requests, observed outputs, stderr, input/output validation outcomes and independent expected results accompany this report. These tests establish bounded technical behavior, not source truth or professional acceptance.

## Initial results

23 cases: 14 met expectations; nine failures represent five underlying control gaps. `results-initial.json` preserves the first observations. `run_review.py` is reproducible and accepts either rejection or explicit unresolved/withheld output where the expected control permits both.

| Finding | Probe | Observed result | Required treatment |
|---|---|---|---|
| Missing row provenance | `c01/c03/c06/c07/c09-missing-observation-refs` | Removing all observation references while retaining a nonempty unrelated source registry still produces results without a missing-source issue. | Require the documented references on each relevant observation/model input, then validate dates/rights on those references. A nonempty registry does not establish linkage. |
| Unregistered control references | `c09-unknown-approval-refs` | An otherwise feasible trade with nonexistent broker and mandate references produces no control findings. | Validate these two reference fields explicitly against registered usable evidence, retaining unknown evidence as unresolved. |
| Contradictory claim scope | `g02-wrong-subject-source` | An approved exact claim whose source explicitly declares a different object and currency is accepted. | Reject or withhold conflicting source scope. General market/rule references need not claim the portfolio identity; a positive contradiction cannot be ignored. |
| Empty selected tax scope | `c07-empty-lots` | No selected lots produces `draft`, zero economic gain and zero positive-gain tax. | Reject empty selected-lot inputs or identify the missing scope explicitly; zero is not an established result for an unspecified review. |
| Unsupported completion and absent owner | `g01-unsupported-completion` | An applicable overdue obligation marked completed, without completion evidence or an owner, suppresses overdue and has no unresolved issue. | Preserve supplied/unverified completion and ownership gaps explicitly. Evidence linkage does not authenticate completion. |

The examples are synthetic. No real legal thresholds, tax rates, recommendations or market observations are inferred from them.

## Successful independent checks

- C01: range minima 0.6, maxima 1.3, dated outflows USD 90,000 and reserve deficit USD 15,000; missing risk owner remains unresolved.
- C03/C04: 25% growth at 10% expected return plus 75% defensive at 2% yields 4%; supplied covariance produces variance 0.008875 and separately computed square-root volatility. The stress return is -4.5%; 25% illiquid weight breaches the supplied 20% limit. A non-PSD covariance rejects.
- C04: variance 0.01000000000001 breaches a 10% volatility limit even though the displayed volatility rounds to 0.100000000000. The author's variance-comparison repair passed this independent boundary.
- C06: sell 10 units at USD 100 and buy 20 at USD 50; 10 bp fees total USD 2 and ending cash is USD 998. Missing sale-proceeds availability blocks implementation. Its projected cash is conditional; the result should not be treated as established settlement funding.
- C07: a USD 225 gain and USD 150 loss yield USD 75 economic gain; only the positive-gain estimate, USD 45 at the supplied 20% rate, is recognized. A related purchase exactly 30 days after sale is flagged; 31 days before sale is excluded. No loss deduction is recognized.
- C09: USD 6,000 and USD 1,000 notionals yield quoted costs USD 7.20 and USD 0.30. 5% ADV participation breaches a supplied 4% limit.
- G01: supplied final/applicable, missing-fact and proposed rules remain distinct; an applicable open overdue obligation is flagged.
- G02: unsupported text with a known source ID is withheld; publication remains unauthorized. A native audience restriction rejects. Text restricted from the intended public audience is withheld. The artifact itself remains internal-review; its internal review identifiers are not an external publication projection.
- Detached-original reconstruction rejects a fabricated cash result.

## Scope and limits

The review did not audit tax law, authenticate approval records, evaluate an optimizer, exercise execution systems or certify production readiness. It did not modify the author's packages. Fixes and replays, if performed, are recorded in `results.json`; the initial failures remain in `results-initial.json`.

## Repair replay

The package author repaired all five reported classes and the independent runner was rerun on the same 23 requests. All 23 now meet the predeclared expected behavior; `results.json` records the repaired results. The initial failure observations remain unchanged in `results-initial.json`. Six regression methods were added to the portfolio suite covering the five control classes and the near-threshold volatility boundary. No package implementation was changed by this reviewer.
