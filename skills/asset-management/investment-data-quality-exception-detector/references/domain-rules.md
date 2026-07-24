# Domain Rules — investment-data-quality-exception-detector

Deterministic data-quality **checks** and how their exceptions map to a **queue priority
band**. Thresholds, required-factor sets, and per-type severities are **configuration**
(versioned, owned by the investment-data governance team), not hard-coded judgments, and are
never tuned to an individual instrument. The engine detects and prioritizes; it never
corrects, suppresses, or chooses a value.

## Check taxonomy

| Check | Fires when (default config) | Evidence attached | Reference-data conflict? |
| ----- | --------------------------- | ----------------- | ------------------------ |
| `stale_price` | Price as-of older than `price_max_age_days` (default 5) vs snapshot `as_of`, OR price unchanged for `price_unchanged_max_days` (default 5) consecutive observations | Price row + as-of + age/unchanged count | No |
| `implausible_move` | `abs((price − prev_price) / prev_price)` exceeds the per-asset-class band (`move_band` default: equity 0.25, bond 0.10, else 0.20) | Price + prev_price + return + band | No |
| `absent_factor` | A held instrument is missing a value for a factor named in its `required_factors` (or the config set for its asset class) | The missing factor name(s) | No |
| `duplicate_instrument` | Two or more distinct instrument keys resolve to the same non-empty identifier (ISIN → CUSIP → SEDOL → ticker) | The colliding keys + shared identifier | No |
| `conflicting_classification` | The same instrument + scheme has distinct non-empty values across feeds | The differing values + feeds | **Yes** → reconciler |
| `broken_mapping` | A mapping row is `resolved: false`, OR a price/factor/classification row references an instrument key with no instrument record (dangling) | The unresolved target / dangling key | Identity → steward |

Checks are **independent and additive**; each exception is reported on its own with its own
evidence. There is no opaque composite "quality score".

## Severity (per exception)

Base severity comes from the versioned config (`severity` map); defaults:

| Check | Base severity |
| ----- | ------------- |
| `broken_mapping` | High |
| `implausible_move` | High |
| `stale_price` | Medium |
| `conflicting_classification` | Medium |
| `duplicate_instrument` | Medium |
| `absent_factor` | Low |

**Escalation (documented, deterministic):** a `stale_price`, `implausible_move`, or
`broken_mapping` exception on an instrument marked `nav_impacting: true` (held with material
weight and feeding valuation) escalates one band, up to `Critical`. No other escalation
exists; severity is never tuned per instrument outside the config.

## Priority mapping (deterministic, documented)

Let `rank = {Low:1, Medium:2, High:3, Critical:4}`. Over the exception set:

| Queue band | Rule |
| ---------- | ---- |
| **None** | No exceptions |
| **P1** | Any `Critical` exception, OR ≥ `p1_high_count` (default 3) exceptions at High-or-above |
| **P2** | Top severity is High |
| **P3** | Top severity is Medium |
| **P4** | Top severity is Low |

`queue_priority` is a **work-ordering suggestion for the analyst**. It is not a determination
that the data is wrong, and it never triggers a correction or a feed write.

## Routing (deterministic)

| Exception type | `route_to` |
| -------------- | ---------- |
| `conflicting_classification` | `investment-vendor-feed-reconciler` (approved-source disagreement — reconcile field-level; the reconciler also does not choose the canonical value) |
| `duplicate_instrument`, `broken_mapping` | `security-master-enricher` / security-master steward (identity + mapping) |
| `stale_price`, `implausible_move`, `absent_factor` | `investment-data-analyst-review` (work with the source owner) |

## Hard boundaries (fail closed)

- Never **correct, override, fill, or normalize** a value; the queue carries no
  `corrected_value`, `override_value`, or `canonical_value` field.
- Never **suppress, waive, dismiss, or close** an exception; every emitted exception has
  `status: open`.
- Never **choose the canonical feed** or state "the correct value is …"; disagreements are
  routed, not resolved.
- Never provide **personalized investment advice** or a NAV/trade instruction from a
  detection.
- Thresholds/severities come only from the recorded `config_version`.

## Reproducibility

`exception_queue_id` binds the queue to the exact snapshot, **config version**, and run.
Re-running with the same inputs and config reproduces the same exceptions, severities,
routing, and `queue_priority`.
