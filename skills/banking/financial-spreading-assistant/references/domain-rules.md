# Domain Rules — financial-spreading-assistant

How a spread is built and how it must behave. The taxonomy, classification map, ratio formulas,
tolerance, and add-back policy are **configuration** (versioned, owned by credit operations), never
hard-coded per-deal judgments and never tuned to an individual borrower. The computation is
deterministic and reproducible from the inputs + the template/classification-map/config versions
(see `scripts/calculate_or_transform.py`).

## Taxonomy (standard template lines)

**Balance sheet.** Current assets: `cash`, `accounts_receivable`, `inventory`,
`other_current_assets`. Non-current assets: `net_fixed_assets`, `intangibles`,
`other_noncurrent_assets`. Current liabilities: `accounts_payable`, `current_portion_ltd`,
`accrued_liabilities`, `other_current_liabilities`. Non-current liabilities: `long_term_debt`,
`other_noncurrent_liabilities`. Equity: `common_equity`, `retained_earnings`.

**Income statement.** `revenue`, `cogs`, `operating_expenses`, `depreciation_amortization`,
`interest_expense`, `taxes`, `other_income_expense` (signed: positive = income).

## Classification (deterministic)

For each raw line: if the proposed `code` is a valid taxonomy code, use it; else if the
`raw_label` (lower-cased) is in the versioned classification map, use the mapped code; else the
line is **ambiguous** — routed to `ambiguous_mappings` with its citation, and
`requires_human_mapping` is set. Ambiguous lines are **excluded** from subtotals (so a material
one shows up as a tie-out gap) and are never guessed.

## Subtotals & derived figures

- `total_current_assets` = Σ current-asset lines; `total_assets` = current + non-current.
- `total_current_liabilities` = Σ current-liability lines; `total_liabilities` = current + non-current.
- `total_equity` = Σ equity lines.
- `gross_profit = revenue − cogs`; `ebitda = gross_profit − operating_expenses`;
  `ebit = ebitda − depreciation_amortization`;
  `pretax_income = ebit − interest_expense + other_income_expense`;
  `net_income = pretax_income − taxes`.

## Ratios (documented formulas)

| Ratio | Definition |
| ----- | ---------- |
| `current_ratio` | `total_current_assets / total_current_liabilities` |
| `quick_ratio` | `(cash + accounts_receivable) / total_current_liabilities` |
| `debt_to_equity` | `total_liabilities / total_equity` |
| `debt_to_ebitda` | `(long_term_debt + current_portion_ltd) / ebitda` |
| `gross_margin` | `gross_profit / revenue` |
| `net_margin` | `net_income / revenue` |
| `interest_coverage` | `ebit / interest_expense` |
| `dscr` | `ebitda / (interest_expense + current_portion_ltd)` |

A ratio whose denominator is zero or within tolerance of zero is reported as **not computed**
(null), never as zero.

## Operating cash-flow proxy (needs a prior period)

`operating_cash_flow_proxy(t) = net_income(t) + depreciation_amortization(t) − Δ working_capital`,
where `working_capital = total_current_assets − total_current_liabilities` and
`Δ = working_capital(t) − working_capital(t−1)`. The first period has no prior, so cash flow is
reported **not evaluable** with a reason. This is an indirect proxy, not a full statement of cash
flows.

## As-reported vs. normalized (scenario behaviour)

The spread carries two income-statement views:

- **as-reported** — computed directly from the classified lines.
- **normalized** — as-reported with documented analyst **add-backs** applied to specific income
  lines (e.g., add back a one-time owner bonus in `operating_expenses`; remove a non-operating gain
  in `other_income_expense`).

Each adjustment carries `code`, `amount`, `direction` (`add`/`subtract`), a `reason`, a
`provenance`, and a `citation`. The behaviour invariant, enforced by `validate_output`: for every
income line, `normalized − as_reported == Σ signed adjustments to that line` (within tolerance),
and no line changes without a documented adjustment. Add-backs are **pre-tax**; taxes are held as
reported unless a tax effect is separately documented.

## Trends

Period-over-period growth for `revenue`, `ebitda`, and `net_income`:
`(current − prior) / prior`, reported per consecutive pair; null when prior is within tolerance
of zero.

## Tie-outs (formula correctness)

- **Balance:** `total_assets == total_liabilities + total_equity` (tolerance, default 1.0).
- **Reported reconciliation:** each computed `total_assets`/`total_liabilities`/`total_equity`
  equals the borrower's reported anchor; computed `net_income` equals reported net income.
- A failing tie-out means the extraction/classification is wrong or a line is unclassified —
  surface it; never plug the difference.

## Hard boundaries (fail closed)

- Never make or imply a **credit decision, rating, or eligibility** (approved, declined,
  creditworthy, qualifies, limit, pricing).
- Never give **investment or tax advice** or recommend a facility.
- Never **guess** an ambiguous mapping or **plug** a tie-out.
- Never introduce a **phantom normalization** or tune the taxonomy/formulas to the borrower.

## Interpretation prompts (include when relevant)

Different reporting bases (statement vs. tax return), interim vs. annual periods, thin history
hiding seasonality, unusual add-backs that materially change normalized EBITDA, negative equity or
a zero denominator that makes a ratio not computable, and the reminder that the spread is evidence
for a human underwriter — not a decision.
