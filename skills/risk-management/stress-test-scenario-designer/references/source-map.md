# Source Map — stress-test-scenario-designer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Stress-testing / ICAAP-ILAAP **standard + scenario config** (versioned) | Approved severity bands, plausibility calibration, transmission betas, binding-constraint limits | Read-only |
| 2 | **Risk register & limits** | Material risk drivers, binding constraints, appetite/limit context | Read-only |
| 3 | **Finance & operational data** | Starting values (CET1, LCR, balances), portfolio exposures for driver selection | Read-only |
| 4 | **Loss events & scenario library** | Historical severity anchors, prior scenarios to avoid duplication | Read-only |
| 5 | **Third-party / concentration inventory** | Dependency and concentration drivers for transmission channels | Read-only |
| 6 | Macro / market **reference data** | Historical factor ranges to sense-check severe-but-plausible bands | Read-only |

Never substitute a modelled or assumed value for an approved config value. If the standard,
the config, and a data source conflict, cite all and flag for the reviewer; do not resolve
silently.

## Citation format

`{system}:{ref}@{version|date}` — e.g. `stress-cfg:cet1.betas@2026.07`,
`finance:cet1_start=11.9@2026-06-30`. Every projected impact cites the config version of the
betas and the starting value used.

## Freshness / effective dates

- The scenario config (bands, plausibility, betas, limits) is a **versioned contract**; the
  pack records the `config_version` so a design is reproducible.
- Starting values (CET1, LCR, exposures) carry an as-of date; state it in the output.
- The `severely_adverse` shock must clear the current severe floor for each factor — floors
  are refreshed with the calibration, not chosen per-run.

## Least-privilege operations (deployment)

- `stresscfg.get(version)` → severity bands, plausibility floors/ceilings, transmission
  betas, binding-constraint limits.
- `riskregister.drivers()` → material risk drivers and binding constraints.
- `finance.starting_values(metric, as_of)` → CET1, LCR, and related starting points.
- `scenariolib.list()` → prior/approved scenarios (to avoid duplication).
All read-only, deterministic, durable `design_id`, below the fixed timeout; page large driver
or exposure sets as resumable stages. The skill computes and evidences a **candidate** design;
it writes nothing to a system of record.
