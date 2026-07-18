# Source Map — credit-memo-drafter

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Credit policy** (controlled content) | Applicable requirements, DSCR floor, leverage cap, exception rules | Read-only |
| 2 | **Credit agreement / covenant** records | Covenant definitions, thresholds, tested mechanics | Read-only |
| 3 | **Approved financial spread** (from spreading) | CFADS, debt service, EBITDA, total debt, reported ratios | Read-only |
| 4 | **Borrower financials & tax returns** (document intelligence) | Supporting statement/return evidence | Read-only |
| 5 | **Collateral / appraisal** records | Appraised value, advance rate, LTV inputs | Read-only |
| 6 | **Risk-rating** system | Approved obligor/facility grade and model | Read-only |
| 7 | **Loan origination / CRM** | Facility request, purpose, relationship context | Read-only |
| 8 | **Credit-memo template + policy config** (versioned) | Required sections, thresholds, approval matrix | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `spread:OB-4210@FY2025;v3`,
`creditagreement:CA-7788;s5.1(a)`, `collateral:appraisal=APR-1121@2026-05-30`,
`policy:credit-policy-2026.05#DSCR`. Every material figure in the memo cites its source.

## Freshness / effective dates

- The spread, appraisals, and risk grade must be the **currently approved** versions; record
  each source's date/version on the memo.
- Policy and template versions are versioned contracts and are stamped on every draft so the
  memo is reproducible when a threshold or section set changes.

## Least-privilege operations (deployment)

- `policy.get('credit-policy', version)`, `template.get('credit-memo-tpl', version)` — read-only.
- `spread.read(obligor_id, period)`, `covenants.read(agreement_id)` — read-only.
- `collateral.read(obligor_id)`, `riskrating.read(obligor_id)`, `los.read(app_id)` — read-only.
No mutation from this skill. The finished draft is *proposed* to the underwriter's workflow via
the approval broker; it is never written to a system of record here.
