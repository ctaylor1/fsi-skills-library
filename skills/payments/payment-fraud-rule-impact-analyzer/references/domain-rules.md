# Domain Rules — payment-fraud-rule-impact-analyzer

Orientation: estimate a rule change's effect on a labeled sample so a human can weigh the
fraud-catch vs false-positive tradeoff. Estimate only; never deploy or decision.

## Rule evaluation (deterministic)
- A rule is `{field, op, threshold}` with `op ∈ {">=", ">", "<=", "<", "=="}`.
- A txn is **blocked** when `txn[field] op threshold` is true, else **allowed**.
- Unsupported op/field → fail closed (no guessed evaluation).

## Metrics (deterministic)
| Metric | Definition |
| ------ | ---------- |
| `blocked_now` / `blocked_proposed` | Count of blocks under each rule |
| `newly_blocked` / `newly_allowed` | allow→block / block→allow between rules |
| `decline_rate` | blocks / sample size, per rule; `delta` = proposed − now |
| Confusion (per rule) | `caught_fraud` (fraud & blocked), `missed_fraud` (fraud & allowed), `false_positives` (legit & blocked), `true_allows` (legit & allowed) |
| Confusion deltas | proposed − now for each cell |

Unlabeled txns are counted in block metrics but excluded from confusion metrics and reported as
`unlabeled`.

## Reporting (estimate only)
- Every metric is **scoped to the sample**; the output states the sample size and never
  extrapolates to production volumes.
- Both sides of the tradeoff (fraud-catch and false positives) are always reported.

## Hard boundaries (fail closed)
- Never deploy/enable/roll out a rule; never make a live block/allow decision; never impute a
  label; never present a sample estimate as a production forecast or a decision.
