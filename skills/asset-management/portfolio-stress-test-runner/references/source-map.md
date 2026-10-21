# Source Map - portfolio-stress-test-runner

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Approved portfolio / book of record** (PMS/OMS, custodian holdings) | Positions, market values, portfolio base value, currency | Read-only |
| 2 | **Approved risk-factor model** (risk engine, factor taxonomy, duration/beta/spread-duration maps) | Factor definitions, per-position factor sensitivities and convexities, `model_version` | Read-only |
| 3 | **Approved scenario definitions** (`stress-test-scenario-designer` / approved scenario library) | Scenario shocks, type (historical/hypothetical), `scenario_set_id`/`scenario_set_version`, approval reference | Read-only |
| 4 | **Approved / official stress engine totals** | Reconciliation target for each computed scenario total | Read-only |
| 5 | **Stress config** (versioned) | Reconciliation tolerance, rounding, attribution ordering, run conventions | Read-only |

A stress run is only as good as its inputs. The portfolio and its sensitivities come from
approved risk systems; **the scenarios themselves are never authored here** - they are
consumed from an approved source and must be human-approved. A filed/book-of-record position
outranks any estimate; a conflict is recorded as an explicit, sourced note, never silently
resolved.

## Citation format

`{source}:{ref}@{date}` - e.g. `pms:holdings@2026-07-15`,
`risk:duration-map@2026-06`, `scenario-designer:SCEN-SET-2026Q3/HIST-GFC-2008@2026-07-10`.
Each position, factor sensitivity, and scenario definition carries a `provenance` (source
class) and a `citation` (specific ref+date). Every scenario also carries its
`scenario_set_id`, `source`, and `approval_ref`. `scripts/validate_output.py` rejects any
assumption missing provenance or citation, and any scenario not marked approved.

## Freshness / effective dates

- **`as_of`** dates the portfolio and its sensitivities (positions and factor exposures are
  point-in-time); **`run_date`** dates the execution. State both in the output.
- **`scenario_set_version`** binds the run to the exact approved scenario definitions; a new
  scenario set is a new version, never an in-place edit.
- **`model_version`** binds the run to the approved sensitivity model; **`config_version`**
  binds tolerance, rounding, and conventions. All three are versioned contracts recorded in
  the run so it is reproducible.
- **`inputs_hash`** binds the run to the exact numeric assumptions and approved scenario
  shocks used; re-running the same inputs reproduces the same `run_id` and the same numbers.
- Do not mix `as_of` sensitivities with a scenario set approved for a different review date
  without recording the mismatch.

## Least-privilege operations (deployment)

- `portfolio.read(portfolio_id, as_of)` -> positions, market values, base value.
- `risk.read_sensitivities(portfolio_id, model_version, as_of)` -> per-position factor
  sensitivities/convexities and factor definitions.
- `scenarios.read(scenario_set_id, version)` -> approved shocks, type, approval reference.
- `engine.totals(scenario_set_id, portfolio_id)` -> official stress-engine totals for
  reconciliation (when available).
- `config.get('stress', version)` -> tolerance, rounding, attribution ordering.

All read-only, deterministic, durable `run_id`, below the fixed timeout. This skill makes
**no writes**; delivery to a committee, board pack, or risk system is a separate,
human-approved step.

## Executable input additions

Use [phase1-contract.md](phase1-contract.md) for the current required fields, scope and detached-original validation. The service calls above are integration contracts; the bundled scripts do not implement those connectors. Source binding proves reproducibility against supplied records, not their authenticity.
