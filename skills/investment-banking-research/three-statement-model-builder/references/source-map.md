# Source Map — three-statement-model-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed financials** (10-K/10-Q, audited statements, filing intelligence) | Base-year income statement and balance sheet; historical margins, working-capital days, D&A, capex, debt terms, tax | Read-only |
| 2 | **Management guidance / operating model** (approved deal or coverage model, mgmt outlook) | Forward driver assumptions (revenue growth, margin, capex plan, capital allocation / payout, debt schedule) | Read-only |
| 3 | **Market/financial data** | Interest rate on debt, share count, financing terms | Read-only |
| 4 | **Research corpus / broker consensus** | Sanity ranges for growth, gross margin, opex ratio, terminal working-capital days | Read-only |
| 5 | **Model config** (versioned) | Scenario-adjustment deltas, tie-out tolerance, driver default ranges, statement conventions | Read-only |

A **forecast driver is only as good as its source.** Every base-year line item and every
driver must resolve to one of the above with a dated citation. A filed number outranks a
management or research estimate; when they conflict, keep the filed figure as the anchor for
the base year and record the estimate as an explicit, sourced driver.

## Citation / source format

Each driver in the input carries a `source` string of the form `{class}:{ref}@{date}` — e.g.
`filings:EXCO-10K-2025;line=sga@2026-03-01`, `research:EXCO-model-2026Q2;driver=revenue_growth@2026-07-10`,
`mgmt:capital-allocation policy@2026-05-02`. `scripts/validate_output.py` requires a
non-empty `source` on **every** assumption and rejects the model otherwise; it also confirms
the full required-driver set is covered.

## Freshness / effective dates

- The **as_of** date anchors the base period and the driver vintage; state it in the output.
- **config** (scenario deltas, tolerance, driver default ranges, conventions) is a
  **versioned contract**; the output records `config_version` so a model is reproducible.
- The base-year statements are point-in-time filed actuals; do not mix reporting periods
  within one base year.
- The `inputs_hash` binds the model to the exact numeric assumptions used; re-running the
  same inputs reproduces the same numbers.

## Least-privilege operations (deployment)

- `filings.read(company_id, statement, period)` → base-year income-statement and
  balance-sheet lines with refs.
- `model.read(model_id)` → approved coverage / operating-model driver outputs.
- `marketdata.get(company_id, as_of)` → interest rate, share count, financing terms.
- `config.get('three-statement', version)` → scenario deltas, tolerance, driver ranges,
  conventions.

All read-only, deterministic, durable `model_id`, below the fixed timeout. This skill makes
**no writes**; delivery to a client, data room, or CRM is a separate, human-approved step.
