# Domain Rules — reserving-analysis-assistant

Loss-development logic applied by
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). All parameters
(methods, tail factors, large-loss thresholds) are a **versioned contract**
(`dataset_version`); the defaults below are illustrative and must be confirmed against the
current actuarial parameter set at deployment. This reference does not select reserves and
does not opine on adequacy.

## Approved development methods

| Method key | Description |
| ---------- | ----------- |
| `volume-weighted` | Chain-ladder age-to-age factor = Σ C(i, j+1) ÷ Σ C(i, j) over origins with both periods (default). |
| `simple-average` | Chain-ladder age-to-age factor = mean of individual C(i, j+1) ÷ C(i, j) link ratios. |

Any other method key is unapproved; the output screen rejects it. Bornhuetter-Ferguson and
Cape-Cod are out of scope for this skill's automated engine and remain actuarial judgment.

## Deterministic computations

1. **Age-to-age factors.** For each development transition dev *j* → *j+1*, compute the
   selected-method factor over the origins that have both periods.
2. **Cumulative development factor (CDF).** From development age *k* to ultimate,
   `CDF(k) = tail × ∏ f(j) for j ≥ k`. The tail factor is applied once.
3. **Indicated ultimate.** For each origin, `ultimate = latest_diagonal × CDF(latest_age)`.
   `reported = latest_diagonal`. `IBNR = ultimate − reported`. Totals are the sum over
   origins; ultimate must equal reported + IBNR at every level (tie-out).
4. **Severity / frequency** (only when supplied). `severity = ultimate_losses ÷
   ultimate_counts`; `frequency = ultimate_counts ÷ earned_exposure`.
5. **Large-loss summary.** Claims with `amount ≥ large_loss_threshold` are counted, totalled,
   and listed for the actuary; a flag is set. Large losses are surfaced, never smoothed away.
6. **Uncertainty (indicative).** A min-max link-ratio range: low ultimate uses the minimum
   observed link ratio at each development period, high uses the maximum. This is an
   indicative sensitivity, **not** a statistical confidence interval or a reserve-range
   opinion.

## Status precedence

`needs-data` (fewer than two development periods, or an undefined factor from a zero
denominator) → `anomaly-flagged` (paid cumulative decreases, or incurred drops > 20%
period-over-period) → `draft-analysis`. Only `draft-analysis` is `packageable`.

## Hard boundaries (fail closed)

- No **reserve selection** and no **booking** of IBNR/reserves to any ledger.
- No **reserve-adequacy opinion** and no **Statement of Actuarial Opinion**.
- No **filing, signing, or submission** to a board, regulator, or auditor.
- No **unsupported assertion** — every figure ties to the triangle/data and cites its
  source; ultimate = reported + IBNR.
- No **fabricated or smoothed data** — missing or anomalous data is reported, never invented.

## Exhibit — required contents

`dataset_version` and `valuation_date`; per-segment method, tail, and development factors;
CDFs; per-origin reported / indicated ultimate / indicated IBNR with citations; totals;
severity/frequency where available; large-loss summary; indicative uncertainty range;
assumptions and limitations; and the actuarial review/approval block (all sign-offs pending).
