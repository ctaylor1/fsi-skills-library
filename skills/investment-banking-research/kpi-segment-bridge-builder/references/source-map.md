# Source Map - kpi-segment-bridge-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed financials** (10-K/10-Q/20-F, audited statements, filing intelligence) | Reported revenue/margin totals, segment notes, the beginning and ending anchors of every bridge | Read-only |
| 2 | **Disclosed KPI supplements / MD&A** (issuer KPI packs, earnings supplements, MD&A revenue and margin bridges, constant-currency tables) | Disclosed bridge components: volume, price/rate, FX, M&A/scope, mix; disclosed units and ARPU for volume-price bridges | Read-only |
| 3 | **Approved mapping registry** (versioned; `mapping_version`) | The only permitted reclassifications/re-mappings (segment realignments, constant-currency, inorganic carve-outs); each carries a `mapping_id`, `status`, and `effective_date` | Read-only |
| 4 | **Bridge config** (versioned; `config_version`) | Decomposition convention, tie-out tolerance, contribution rounding, allowed source types | Read-only |
| 5 | **Entity resolution** | Resolve the issuer / segment identifiers behind the masked `company_id` | Read-only |

A **bridge component is only as good as its disclosure.** Every anchor and component resolves
to one of the above with a dated citation. Filed totals are the anchor; a disclosed component
that conflicts with the filed total is recorded as an explicit, sourced item and the walk must
still reconcile to the filed total. **Nothing forward-looking enters a bridge** (see the source
types below).

## Source-type discipline (HARD BOUNDARY: never forecast)

Every node and component carries a `source_type`. Only **historical / disclosed** types are
admissible: `reported`, `disclosed`, `actual`, `filing`, `audited`, `derived` (a value computed
deterministically from disclosed factors). Forward-looking types are **rejected**:
`forecast`, `projection`, `guidance`, `estimate`, `consensus`, `target`, `budget`, `plan`,
`model-output`. `scripts/validate_input.py` errors on them before any bridge is built and
`scripts/validate_output.py` rejects them in the pack.

## Mapping discipline (HARD BOUNDARY: never normalize beyond approved mappings)

A component may only be reclassified or re-mapped via an **approved** `mapping_id`. The approved
set is a versioned contract (`mapping_version`); each entry has a `status` (must be `approved`)
and an `effective_date`. Any component whose `derivation` is `mapping` must reference an approved,
effective mapping. Discretionary/ad-hoc normalization is a control failure: warned on input,
**rejected** on output, and routed to `financials-normalizer` or accounting policy.

## Citation format

`{source}:{ref}@{date}` - e.g. `filing:FY2025 10-K segment note@2026-02-20`,
`filing:FY2025 10-K MD&A constant-currency table@2026-02-20`,
`kpi:FY2025 KPI supplement units@2026-02-20`. Each entry in the pack's
`assumptions_register` carries `provenance` (source class) and `citation` (specific ref+date);
`validate_output` rejects any entry missing either.

## Freshness / effective dates

- The **prior_period.end** and **current_period.end** define the exact comparison window; a
  bridge only ever compares two **closed, reported** periods.
- **mapping_version** binds the approved reclassifications; **config_version** binds the
  decomposition convention and tolerance. Both are recorded in the pack for reproducibility.
- A mapping is only usable if its `effective_date` is on or before the reporting period; an
  expired or not-yet-effective mapping is treated as unapproved.
- The `inputs_hash` binds the pack to the exact disclosed inputs and mapping set used;
  re-running the same inputs reproduces the same `pack_id` and the same numbers.

## Durable identifiers

- `job_id` - a durable, caller-supplied (or derived) job identifier for the extraction/build.
- `pack_id = kpi-bridge-{company}-{current_period}-{inputs_hash}` - the durable, reproducible
  identifier for the bridge pack that downstream skills cite.

## Least-privilege operations (deployment)

- `filings.read(company_id, statement|segment_note, period)` -> reported totals + segment lines.
- `kpi.read(company_id, period)` -> disclosed KPI supplement (units, ARPU, disclosed bridge lines).
- `mappings.get(mapping_version)` -> approved reclassification registry with status + effective date.
- `config.get('kpi-bridge', version)` -> decomposition convention, tolerance, allowed source types.
- `entity.resolve(company_id)` -> issuer/segment resolution.

All read-only, deterministic, durable `pack_id`/`job_id`, below the fixed timeout. This skill
makes **no writes**; delivery to a client, data room, CRM, or model of record is a separate,
human-approved step.
