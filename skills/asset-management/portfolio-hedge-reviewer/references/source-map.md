# Source Map — portfolio-hedge-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved risk engine / analytics** (sensitivity & scenario service) | Portfolio factor sensitivities and approved-engine reconciliation totals | Read-only |
| 2 | **Approved model registry / model governance** | The sanctioned sensitivity model — its `id`, `version`, and `effective_date` | Read-only |
| 3 | **Portfolio exposure set** (from `portfolio-exposure-analyzer`) | Base-portfolio exposures/sensitivities by factor, with lineage | Read-only |
| 4 | **Hedge specifications** (analyst-defined candidate hedges) | Each candidate hedge's supplied per-factor sensitivities and cost | Read-only |
| 5 | **Approved scenario library** (from `stress-test-scenario-designer`) | The standardized factor shocks each scenario applies | Read-only |
| 6 | **Hedge-analysis config** (versioned) | Factor-unit definitions, tie-out and reconciliation tolerances, reporting units | Read-only |

Every sensitivity, cost, factor-unit definition, and scenario shock must resolve to one of
the above with a dated citation. The **portfolio's own approved sensitivities and the
approved-engine totals are the anchor**; a supplied hedge sensitivity or cost is an input to
be tabulated, never re-derived or priced here. This skill **does not invent hedges,
scenarios, sensitivities, or costs** — all are human-supplied under an approved model.

## Citation format

`{source}:{ref}@{date}` — e.g. `exposure:portfolio-exposure-analyzer run@2026-07-15`,
`model-registry:MR-0421 approved@2026-06-01`, `scn:stress-test-scenario-designer 2026-Q3@…`,
`desk:rates carry@2026-07-14`. Each entry in the packet's `assumptions_register` carries
`provenance` (the source class) and `citation` (the specific ref+date).
`scripts/validate_output.py` rejects any assumption missing either.

## Freshness / effective dates

- The **valuation_date** anchors the portfolio sensitivities, hedge specs, and scenario set;
  state it in the output. Do not mix as-of dates within one packet.
- The **model** is a versioned contract: `model.id`, `model.version`, and
  `model.effective_date` are recorded so the calculation methodology is reproducible; a
  sensitivity produced under a superseded model version is stale — do not mix versions.
- **config** (factor units, tolerances, reporting units) is versioned; the output records
  `config_version`.
- The `inputs_hash` binds the packet to the exact numeric assumptions used; re-running the
  same inputs reproduces the same `packet_id` and the same numbers.
- **case_id** is the durable case/job identifier carried end to end (input → packet →
  handoff), so a packet is traceable across reviews and downstream skills.

## Least-privilege operations (deployment)

- `riskengine.sensitivities(portfolio_id, as_of)` → factor sensitivities + approved totals.
- `riskengine.scenario(portfolio_id, scenario_id, as_of)` → approved scenario shock set.
- `modelregistry.get(model_id, version)` → approved model metadata (version, effective date).
- `config.get('hedge-analysis', version)` → factor-unit definitions, tolerances, units.
All read-only, deterministic, durable `case_id`/`packet_id`, below the fixed timeout. This
skill makes **no writes**; delivery to a portfolio manager, investment committee, trade
ticket, OMS, or risk system of record is a separate, human-approved step.

## Executable input additions

Use [phase1-contract.md](phase1-contract.md) for the current required fields, scope and detached-original validation. The service calls above are integration contracts; the bundled scripts do not implement those connectors. Source binding proves reproducibility against supplied records, not their authenticity.


## Phase 4 supplied full-repricing extension

For explicitly selected `advanced-derivatives`, use [the separate advanced contract](advanced-derivatives.md). Preserve full-book engine/benchmark binding and the no-fallback boundary; the first-order method above is not a complex derivative pricer.
