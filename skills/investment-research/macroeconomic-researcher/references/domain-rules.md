# Point-in-time selection, transformations and interpretation

For each (series_id, period_end), retain the latest supplied release no later
than both knowledge_cutoff and as_of. Economic periods must also not exceed
as_of. A date-only release cannot prove intraday availability against a
timestamp cutoff, or vice versa; record an exclusion and do not manufacture a
midnight. Superseded and future releases appear only as identities and exclusion
reasons. With no eligible release, the series or comparison is unavailable.
Selecting the latest eligible null preserves missingness; an older nonnull
release is not silently substituted. The supplied inventory can omit releases,
so selection does not establish an exhaustive external publication history.

The first-to-latest eligible supplied revision delta is latest minus first in
the series unit. It is not necessarily the revision from the official initial
release. For a percent rate, the delta unit is percentage-point.

For two selected endpoints in one immutable series basis:

- Difference = end minus start, in original units; a percent rate difference is
  in percentage points.
- Percent change = 100 × (end/start − 1); start must be positive and end
  nonnegative. Rate-series percent changes are unsupported; use a difference.
- Annualized percent change = 100 × ((end/start)^(12/elapsed calendar months)
  − 1), with positive endpoints and seasonal comparability. The method rejects
  annualization of explicitly unadjusted series. A one-quarter comparison uses
  exponent 4; a monthly comparison uses 12. Annualization is a convention, not
  evidence that the pace will persist.

No cross-series calculation, rebasing, frequency alignment, seasonal adjustment,
currency conversion, growth contribution or aggregation is performed. Split a
series when geography, unit, price base, frequency or seasonal basis changes;
do not put incompatible observations beneath one series identity. The engine
cannot authenticate caller-supplied basis declarations.

For a research note, assess the level and breadth of the change, revision
effects, base effects, measurement caveats and evidence against the proposed
growth/inflation/policy interpretation. Keep forecasts, consensus provider
claims and scenarios separate from observed data. Missing consensus is not
zero consensus or an estimated surprise. Do not infer causality, a regime,
scenario probabilities, policy commitments or investment recommendations from
the arithmetic alone. State the next release or falsifier needed to update the
view and retain any unavailable required comparison as partial coverage.
