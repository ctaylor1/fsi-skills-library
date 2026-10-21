# Source Map — dcf-modeler

`forecast_mode` may only be `standalone-ratio-fcff`; omitted selects that declared method. `upstream_model_id` and `forecast_rows` are rejected because no native adapter is implemented. `bridge` must contain all five sourced components including genuine zeros.


## Version 0.2.0 contract

The native result is a closed calculation record. Retain the original input separately and validate with `python3 scripts/validate_output.py RESULT.json --input ORIGINAL.json`; `--selftest` loads both bundled examples. Computation validates input first. Finite JSON numbers, valid dates, supported domains and unique identifiers are enforced; duplicate JSON keys are rejected. Output validation reconstructs from the original and rejects omitted, altered or extra results, including flags/counts/statuses. Keep author narrative and workflow envelopes outside the native result. Source binding establishes deterministic fidelity to supplied inputs, not source authenticity, data rights, economic validity, institutional acceptance or independent assurance.


## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed financials** (10-K/10-Q, audited statements, filing intelligence) | Base-year revenue, historical margins, D&A, capex, tax, balance-sheet bridge items | Read-only |
| 2 | **Management guidance / model inputs** (approved deal or coverage model, mgmt outlook) | Forward driver assumptions (growth, margin, capex plan) | Read-only |
| 3 | **Market/financial data** | Risk-free rate, beta, share count, cost of debt, comparable exit multiples | Read-only |
| 4 | **Research corpus / broker consensus** | Sanity ranges for growth, margin, terminal multiple, ERP | Read-only |
| 5 | **Valuation config** (versioned) | Scenario-adjustment deltas, discount convention, tie-out tolerance, default ranges | Read-only |

A **forecast driver is only as good as its source.** Every driver, WACC component, terminal
input, and bridge item must resolve to one of the above with a dated citation. A filed
number outranks a management or research estimate; when they conflict, keep the filed figure
as the anchor and record the estimate as an explicit, sourced override.

## Citation format

`{source}:{ref}@{date}` — e.g. `filing:FY2025 10-K note 14@2026-02-20`,
`mgmt:FY26 guidance call@2026-05-02`, `mkt:UST 10Y@2026-07-15`. Each entry in the model's
`assumptions_register` carries `provenance` (the source class) and `citation` (the specific
ref+date). `scripts/validate_output.py` rejects any assumption missing either.

## Freshness / effective dates

- The **valuation_date** anchors WACC market inputs and the share count; state it in the output.
- **config** (scenario deltas, tolerance, discount convention, default ranges) is a
  **versioned contract**; the output records `config_version` so a model is reproducible.
- Market inputs (risk-free, beta) are point-in-time as of the valuation date; do not mix
  dates within one WACC.
- The `inputs_hash` binds the model to the exact numeric assumptions used; re-running the
  same inputs reproduces the same `model_id` and the same numbers.

## Least-privilege operations (deployment)

- `filings.read(company_id, statement, period)` → bounded statement lines with refs.
- `marketdata.get(company_id, as_of)` → risk-free, beta, share count, cost of debt, multiples.
- `model.read(model_id)` → approved three-statement / operating-model driver outputs.
- `config.get('dcf', version)` → scenario deltas, tolerance, discount convention, ranges.
All read-only, deterministic, durable `model_id`, below the fixed timeout. This skill makes
**no writes**; delivery to a client, data room, or CRM is a separate, human-approved step.
