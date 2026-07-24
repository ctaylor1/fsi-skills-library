# Domain Rules — actuarial-data-lineage-checker

Deterministic reconciliation of actuarial input data. The firm's data-definition registry and
reconciliation config (versioned) govern; nothing is corrected or assumed.

## Break taxonomy
Records are keyed by `(key, metric, period)` with `value`, `definition_version`, `source_ref`.

| Break type | Fires when | Evidence |
| ---------- | ---------- | -------- |
| `duplicate` | Same `(key, metric, period)` appears more than once in the current dataset | The duplicate record refs |
| `missing_period` | An `expected_period` for a (key, metric) is absent from current | Expected vs present periods |
| `definition_shift` | `definition_version` differs from the config baseline (or from the prior period for the same key/metric) | Current vs baseline/prior version |
| `unexplained_movement` | \|current − prior\| / \|prior\| > `movement_pct` (default 20%) AND no documented reason, with a non-zero prior | Current, prior, % change |
| `new_series` | A (key, metric, period) with no prior value | Reported factually (not a movement) |

Config (`movement_pct`, `expected_periods`, `definition_baseline_version`) is a **versioned
contract**; the output records the versions used.

## Disposition mapping (review-only)
- `clean` — no breaks.
- `breaks-for-review` — ≥1 break. A triage suggestion for the actuary/data owner, **not** a
  correction, assumption selection, or certification.

## Hard boundaries (fail closed)
- Never alter/correct source data; never select an assumption/method; never certify reserve
  data or issue an opinion.
- Guard division by a zero prior (classify as `new_series`), and treat an absent definition
  version as not-evaluable for `definition_shift`.
