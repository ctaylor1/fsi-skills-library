# Source Map — nav-preparation-tie-out

## Source hierarchy (per component)

A NAV tie-out compares the fund's **book of record** against one or more **independent
verifier** sources. Neither is subordinate in truth — a break is a disagreement to be
evidenced, not adjudicated — but each component has a defined verifier it is tied out
against (configurable via `config.component_sources`).

| Rank | Source (MCP integration) | Position of record for | Access |
| ---- | ------------------------ | ---------------------- | ------ |
| 1 | **Fund accounting book of record (ABOR)** | The fund's own positions, prices, accruals, income, expenses, shares, cash | Read-only |
| 2 | **Custodian** | Independent positions and cash (settled/held) | Read-only |
| 3 | **Administrator / transfer agent** | Independent accruals, income, expenses, shares outstanding | Read-only |
| 4 | **Approved pricing source** | Independent security prices (approved vendor / hierarchy) | Read-only |
| 5 | Tie-out **config** (versioned) | Tolerances, materiality, date cutoff, component→verifier mapping | Read-only |
| 6 | Prior-cycle **tie-out** (durable `tie_out_id`) | Carry-forward of open reconciling items | Read-only |

Default component→verifier pairing (`config.component_sources`):
`position→custodian`, `cash→custodian`, `price→pricing`, `accrual→administrator`,
`income→administrator`, `expense→administrator`, `shares→administrator`.

The skill classifies and evidences the disagreement; it **never decides which source is
right**, never selects a price, never strikes NAV, and never posts an entry. If sources
conflict, cite both and flag for the fund accountant.

## Input schema (validated by `scripts/validate_input.py`)

Top level: `fund`, `share_class` (optional), `as_of` (YYYY-MM-DD), `base_currency`,
`config_version`, `lines[]`, `config{}`.

Each `lines[]` record:
`line_id` (unique across the job), `component` (one of position, price, cash, accrual,
income, expense, shares), `key` (security id, cash account/currency, accrual type, expense
type, share class), `source` (one of book, custodian, administrator, pricing), `value`
(signed numeric — quantity for position/shares, price for price, amount for the rest),
`currency`, `as_of` (YYYY-MM-DD), `source_ref`, `description`.

`config`: `tolerances{per-component}`, `date_tolerance_days`, `materiality{default + per
component}`, `component_sources{component→verifier}`.

## Citation format

`{source}:{source_ref}@{as_of}` — e.g. `book:abor;pos;acct=LOTUS;sec=SEC-BBB@2026-06-30` and
`custodian:custodian;holdings;sec=SEC-BBB@2026-06-30`. Every break carries lineage citations
to the book and/or verifier rows it was derived from (prefix in
`book:` / `custodian:` / `administrator:` / `pricing:`).

## Freshness / effective dates

- `config` (tolerances, materiality, date cutoff, component→verifier map) is a **versioned
  contract**; the output records `config_version` so a tie-out is reproducible.
- `as_of` fixes the valuation date. Matched values whose source `as_of` dates differ beyond
  `date_tolerance_days` are **timing differences** — documented reconciling items expected to
  clear next cycle, not repaired.
- `input_fingerprint` (SHA-256 of the normalized inputs + config) makes the `tie_out_id` a
  pure function of the inputs — re-running the same inputs is idempotent.

## Least-privilege operations (deployment)

- `abor.read(fund, share_class, as_of)` → book positions/prices/accruals/income/expenses/shares/cash.
- `custodian.read(fund, as_of)` → independent positions and cash.
- `administrator.read(fund, share_class, as_of)` → independent accruals/income/expenses/shares.
- `pricing.read(security_ids, as_of)` → approved-source prices (observed, not chosen).
- `config.get('nav-tieout', version)` → tolerances, materiality, cutoff, component→verifier map.
- `tieout.get(tie_out_id)` → prior-cycle open items for carry-forward.

All read-only, deterministic, durable `tie_out_id`, below the fixed timeout; page long
holdings as resumable stages. **No write/strike/price/post operation is bound to this skill.**
