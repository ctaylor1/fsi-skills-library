# Source Map — financial-statement-audit-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **ERP / general ledger** (trial balance) | System of record for account balances; the tie-out base | Read-only |
| 2 | **Subledgers** (AR, AP, inventory, fixed assets, revenue) | Populations for sampling; item-level detail and support | Read-only |
| 3 | **Consolidation / financial-statement package** | Reported captions, groupings, eliminations, disclosures | Read-only |
| 4 | **FP&A / management reporting** | Analytical expectations, budget/prior-year comparatives | Read-only |
| 5 | **Regulatory reporting** | Filed-return figures for cross-reference (not the audit base) | Read-only |
| 6 | **Document & spreadsheet tools** | Client-provided support, confirmations, contracts, memos | Read-only |
| 7 | **Planning parameters** (materiality, tolerable misstatement, reliability factor, sampling config) — **versioned** | Sampling and misstatement evaluation | Read-only |

The ERP/GL trial balance is the tie-out base; the financial-statement package is what is
being tested *against* it. Where a filed regulatory figure and the GL disagree, cite both
and raise an open item — do not silently pick one.

## Citation format

`{system}:{ref}@{period/version}` — e.g. `tb:1200@FY2026`, `fs:balance-sheet@FY2026`,
`subledger:AR:AR-13@FY2026`, `config:audit-wp@2026.07`. Every tie-out, every selection, and
every finding carries at least one citation. An assertion without a citation is an
**unsupported assertion** and `scripts/validate_output.py` fails closed on it.

## Freshness / effective dates

- Read the trial balance and subledgers **as of the reporting date / lock version**; a
  post-close adjustment changes the tie-out base and must re-run.
- Planning parameters (materiality, tolerable misstatement, reliability factor, sampling
  seed) are a **versioned contract** recorded on every working paper for reproducibility.

## Least-privilege operations (deployment)

- `gl.trial_balance(period, version)`, `subledger.read(account, period)` — read-only.
- `fs.package(period)` (captions, groupings), `fpa.comparatives(period)` — read-only.
- `config.get('audit-wp', version)` — materiality/sampling parameters, read-only.
- `docs.read(request_id)` — client-provided support, read-only.

No mutation from this skill. The working paper is a **draft artifact**; recording sign-off,
delivering to the file, or issuing to a regulator/client is a separate, human-approved step
via the approval broker — never performed here.
