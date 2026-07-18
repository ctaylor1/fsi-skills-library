# Source Map — market-sizing-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Official statistics / regulator data** (census, central bank, government agency, supervisory data) | Market universe, establishment/population counts, official category spend | Read-only |
| 2 | **Company filings** (10-K/20-F, prospectus, data-room financials) | Actual revenue, pricing/ARPU, unit economics for the subject and comparables | Read-only |
| 3 | **Third-party industry research** (analyst market reports, trade associations) | Category aggregates, growth rates, adoption/attach rates | Read-only |
| 4 | **Management / internal figures** (CIM projections, go-to-market plan) | Obtainable share, capture rates, plan-based assumptions | Read-only |
| 5 | **Analyst-derived estimate** (our own build-up/triangulation) | Segment filters, bridges where no external source exists | Derived |

Higher-tier sources take precedence for the same quantity. A serviceable/obtainable **ratio**
sourced from tier 4–5 must be labeled as an assumption, never presented as an official figure.
When two sources conflict for one driver, cite both and express the disagreement as the
low–high range rather than silently picking one.

## Assumption provenance and source tier (required)

Every driver that feeds the model carries:

- `provenance` — a specific citation (`{tier}:{ref}`), e.g.
  `official-statistic:US Census County Business Patterns 2024`,
  `company-filing:comparable vendor 10-K FY2025 pricing disclosure`,
  `industry-research:PayrollTech Market Report 2026 p.12`,
  `internal-assumption:go-to-market plan v3`.
- `source_tier` — one of `official-statistic`, `company-filing`, `industry-research`,
  `management-estimate`, `internal-assumption`, `analyst-estimate`.

`scripts/validate_output.py` fails closed if any register entry lacks provenance **or**
source_tier. The lowest-tier driver in each chain is the one to stress in the uncertainty range.

## Citation format

`{system}:{ref}@{date}` for retrieved records — e.g.
`filings:cik=0000000000;form=10-K;fy=2025@2026-03-01`. Driver-level provenance additionally
records the `{tier}:{ref}` string shown above so a reviewer can trace every number to a source.

## Freshness / reproducibility

- Scenario definitions, `primary_method`, `triangulation_tolerance_pct`, and numeric tolerance
  are a **versioned config contract**; the output records `config_version` so a sizing is
  reproducible.
- The output records the exact `as_of` date and the market/segment definitions used.
- `sizing_id` binds the output to inputs + drivers + config version. Re-running the same inputs
  and config reproduces every scenario, tie-out, and triangulation gap exactly.

## Least-privilege operations (deployment)

- `marketdata.get(market, as_of)` → category aggregates / official statistics (bounded, paged).
- `filings.read(entity, form, period)` → pricing/ARPU and actuals for subject and comparables.
- `research.retrieve(topic, as_of)` → industry-research aggregates with citations.
- `entity.resolve(segment|geo|company)` → normalized segment and geography keys.
- `config.get('market-sizing', version)` → scenarios, primary method, tolerances.

All read-only, deterministic, durable `sizing_id`, below the fixed timeout; page long retrievals
as resumable stages. No write path exists in this skill.
