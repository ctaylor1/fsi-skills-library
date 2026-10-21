# Source Map — lbo-model-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Filed financials** (10-K/10-Q, audited statements, filing intelligence) | LTM / base-year revenue and EBITDA, margins, D&A, capex, tax, opening balances | Read-only |
| 2 | **Sponsor / management operating model** (approved deal or coverage model, management case) | Forward operating drivers (revenue growth, EBITDA margin, capex, working capital) | Read-only |
| 3 | **Market/financial data** (leveraged-finance desk, credit markets) | Debt tranche pricing (rate), clearing leverage (turns), fees/OID, entry and exit EV/EBITDA multiples | Read-only |
| 4 | **Data room / credit terms** (lender term sheets, credit agreement drafts) | Amortization terms, cash-sweep percentage, revolver and covenant terms | Read-only |
| 5 | **Research corpus / broker consensus** | Sanity ranges for growth, margin, exit multiple, sector leverage norms | Read-only |
| 6 | **LBO config** (versioned) | Scenario-adjustment deltas, tie-out tolerance, fee and minimum-cash defaults, high-leverage warning threshold | Read-only |

A **model input is only as good as its source.** Every entry assumption, capital-structure
term, operating driver, and exit input must resolve to one of the above with a dated
citation. A filed number outranks a management or research estimate; when they conflict, keep
the filed figure as the anchor and record the estimate as an explicit, sourced override.

## Citation format

`{source}:{ref}@{date}` — e.g. `filing:LTM 2026-Q2 adjusted EBITDA@2026-07-31`,
`mkt:TLB clearing leverage@2026-07-10`, `mgmt:management projection@2026-06`. Each entry in
the model's `assumptions_register` carries `provenance` (the source class) and `citation`
(the specific ref+date). `scripts/validate_output.py` rejects any assumption missing either.

## Freshness / effective dates

- The **entry_date** anchors the entry multiple, LTM EBITDA, and debt pricing; state it in the output.
- **config** (scenario deltas, tolerance, fee/leverage defaults) is a **versioned contract**;
  the output records `config_version` so a model is reproducible.
- Debt pricing (rate, turns, fees) and comparable exit multiples are point-in-time as of the
  entry date; do not mix dates within one capital structure.
- The `inputs_hash` binds the model to the exact numeric assumptions used; re-running the
  same inputs reproduces the same `model_id` and the same numbers.

## Least-privilege operations (deployment)

- `filings.read(company_id, statement, period)` → bounded LTM revenue, EBITDA, D&A, tax, opening balances.
- `marketdata.get(company_id, as_of)` → debt-tranche rates and turns, fees, entry/exit multiples.
- `model.read(model_id)` → approved three-statement / operating-model driver outputs.
- `dataroom.read(deal_id, doc)` → credit terms (amortization, cash sweep, covenants).
- `config.get('lbo', version)` → scenario deltas, tolerance, fee/leverage defaults.

All read-only, deterministic, durable `model_id`, below the fixed timeout. This skill makes
**no writes**; delivery to a client, deal team, data room, or CRM is a separate,
human-approved step.
