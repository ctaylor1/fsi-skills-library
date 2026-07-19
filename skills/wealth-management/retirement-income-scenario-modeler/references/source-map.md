# Source Map — retirement-income-scenario-modeler

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Portfolio accounting / OMS / custodian** | Account balances by tax treatment (taxable, tax-deferred, tax-free) as of the valuation date | Read-only |
| 2 | **Planning engine / client file (CRM)** | Spending need, guaranteed-income estimates (Social Security, pension), ages, longevity horizon, household profile | Read-only |
| 3 | **Approved assumption set / retirement-modeling config** (versioned) | Expected returns, inflation, effective tax rates, scenario deltas, default withdrawal bands, discount/rounding conventions | Read-only |
| 4 | **Product & disclosure data / restrictions** | Product features, fees, and restrictions that bound a modelled strategy | Read-only |
| 5 | **Research / capital-market commentary** | Sanity ranges for returns, inflation, and longevity | Read-only |

An **assumption is only as good as its source.** Every spending figure, return, tax rate,
guaranteed-income amount, and withdrawal parameter must resolve to one of the above with a
dated citation. A custodial balance outranks an estimate; when they conflict, keep the
custodial/anchor figure and record the estimate as an explicit, sourced override. Returns,
inflation, and tax rates are **approved assumptions owned by the planning / model-governance
function**, never the skill's judgment, and are never bent to make a plan "succeed".

## Citation format

`{source}:{ref}@{date}` — e.g. `oms:IRA custody position@2026-07-15`,
`plan:SSA statement estimate@2026-05`, `cfg:CMA 2026.07 balanced`,
`cfg:approved effective tax table 2026.07 ordinary`. Each entry in the model's
`assumptions_register` carries `provenance` (the source class) and `citation` (the specific
ref+date). `scripts/validate_output.py` rejects any assumption missing either.

## Freshness / effective dates

- The **valuation_date** anchors balances and the approved-assumption vintage; state it in the output.
- **config** (returns, inflation, tax rates, scenario deltas, conventions) is a **versioned
  contract**; the output records `config_version` so a model is reproducible.
- Guaranteed-income estimates (SSA, pension) are point-in-time; do not mix vintages within one run.
- The `inputs_hash` binds the model to the exact numeric assumptions used; re-running the same
  inputs reproduces the same `model_id` and the same numbers.

## Least-privilege operations (deployment)

- `portfolio.read(household_id, as_of)` → account balances by tax treatment with refs.
- `plan.read(household_id)` → spending need, guaranteed-income estimates, ages, horizon.
- `config.get('retirement', version)` → returns, inflation, tax rates, scenario deltas, bands.
- `product.read(product_id)` → features, fees, restrictions bounding a modelled strategy.

All read-only, deterministic, durable `model_id`, below the fixed timeout. This skill makes
**no writes**; any recommendation, decision, trade, or delivery to the client / CRM / book of
record is a separate, human-adjudicated step.
