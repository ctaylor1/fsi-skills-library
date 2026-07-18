# Domain Rules — credit-memo-drafter

Orientation references: the bank's commercial **credit policy** and **credit-memo template**
(both versioned contracts), the credit agreement for covenant mechanics, and prudent
underwriting practice (e.g., interagency commercial-lending / CRE guidance). Policy thresholds
below are **defaults**; the deployed `policy_config` is authoritative and versioned. All
figures are deterministic and trace to cited inputs — nothing here is analyst judgment.

## Deterministic metrics

| Metric | Formula | Default policy reference |
| ------ | ------- | ------------------------ |
| **DSCR** | CFADS ÷ total debt service | floor **1.20x**; below floor → observation + exception |
| **Leverage** | total debt ÷ EBITDA | cap **4.00x**; above cap → observation + exception |
| **LTV** | total exposure ÷ appraised collateral value | reported for the underwriter |
| **Advance coverage** | lendable collateral ÷ total exposure | < 1.0 → collateral shortfall observation |
| **Lendable collateral** | Σ (appraised_value × advance_rate) | per-collateral advance rate |

DSCR and leverage are **recomputed from spread primitives** and reconciled to the ratios the
approved spread reported (tie-out). Ratios are rounded to 2 decimals; LTV/coverage to 4.

## Spread tie-out

Recomputed DSCR and leverage must match the spread-reported ratios within
`tie_out_tolerance` (default **0.01** absolute). An out-of-tolerance diff is a **tie-out
break**: the financial section is not yet supportable, the difference is surfaced, and the
memo routes back to spreading. The memo never presents an unreconciled ratio as fact.

## Policy coverage

Every `policy_requirement` with `applies: true` must be **addressed** — either mapped to a
memo section (`addressed_section`) or covered by an `exception_ref` whose exception carries a
mitigant. Any applicable requirement left unmapped is a **coverage gap** and cannot be marked
addressed.

## Covenant headroom

For each covenant: `min` type headroom = tested_metric − threshold; `max` type headroom =
threshold − tested_metric. Negative headroom is a **breach-at-inception** — documented for the
underwriter with its citation, **never waived** by the memo.

## Exceptions

Each policy exception is **documented with a mitigant**; an exception without a mitigant is an
unsupported item (`needs-data`), not an addressed one. The memo records exceptions and
mitigants for the approver to dispose of. Documenting an exception is **not** granting or
waiving it.

## Required approvals (recorded, pending)

Default approver roles: **Underwriter** and **Credit Officer**; add **Credit Committee** when
total exposure ≥ `large_credit_threshold` (default **5,000,000**). All are recorded with
`status: pending`. The draft never self-grants an approval.

## Hard boundaries (fail closed)

- No **credit decision** (approve/decline/adverse action), **pricing commitment**, **booking,
  funding, disbursement, or filing**, or any **system-of-record write**.
- No **granting or waiving** of a policy exception or covenant.
- No **self-granted approval**; approvals stay `pending`/`required`.
- No **unsupported assertion** and no **guessed figure**; missing inputs are `needs-data`.

## Draft memo — required sections

`borrower_overview`, `facility_summary`, `financial_analysis`, `repayment_analysis`,
`collateral_analysis`, `risk_rating`, `covenants`, `policy_exceptions`, `recommendation` —
each present, non-empty, and cited (see [../assets/output-template.md](../assets/output-template.md)).
