# Source Map — valuation-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved pricing / market-data** service | Independent price-verification (IPV) marks, curves, comparables | Read-only |
| 2 | **Valuation record** (ERP/GL, subledger, product-control workpaper) | Reported value, method, fair-value level, inputs, adjustments, overrides | Read-only |
| 3 | **Controlled valuation policy / methodology library** (versioned) | Method appropriateness, hierarchy rules, adjustment and reserve policy | Read-only |
| 4 | **Valuation-review config** (versioned) | Staleness, IPV-tolerance, materiality, comparable-minimum thresholds | Read-only |
| 5 | **Document intelligence** | Approval memos, override authorizations, committee minutes cited as evidence | Read-only |

Never substitute a desk/trader assertion for the independent price or the valuation record.
If the reported value and the independent source conflict, cite both and raise the finding
for the reviewer — do not resolve it silently or restate the mark as correct.

## Citation format

`{system}:{ref}@{date}` — e.g. `ipv:vendor-Xmark;asof=2026-07-15@2026-07-15` or
`val:instrument=OTC-SWAP-338;adjustment=model_reserve@2026-07-15`. Every fired finding cites
the specific evidence row(s) it rests on. When a finding is about a *missing* attribute
(no source_ref, no uncertainty range), the citation points at the valuation-record position
so the gap is still locatable.

## Freshness / effective dates

- Review config and valuation policy are **versioned contracts**; the output records the
  `config_version` used so a review is reproducible.
- Input `source_date` is compared to `as_of`; inputs older than `max_staleness_days` fire
  `input_staleness`. State the exact `as_of` in the output.
- IPV evidence must carry its own `source_date`; a stale IPV is not independent verification.

## Least-privilege operations (deployment)

- `pricing.ipv(instrument_id, as_of)` → independent value + source ref/date.
- `valuation.record(instrument_id, as_of)` → reported value, method, level, inputs,
  adjustments, overrides (bounded, paged).
- `policy.get('valuation', version)` → method/hierarchy/adjustment rules.
- `config.get('valuation-review', version)` → thresholds.
- `docs.get(ref)` → approval/override/committee evidence.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long input
sets as resumable stages. The skill makes **no** writes and stages nothing for execution.
