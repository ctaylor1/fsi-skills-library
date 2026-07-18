# Domain Rules — financials-normalizer

How source financial statements are mapped to a **standard chart-of-accounts taxonomy**,
which normalization **checks** fire, and how the fired set maps to a **readiness band**.
Thresholds are configuration (versioned, owned by the Finance & Controllership / model-data
governance function), not hard-coded judgments, and never tuned to make a particular extract
pass. The firm's chart-of-accounts standard, its normalization/adjustment policy, and the
applicable reporting framework (US-GAAP / IFRS) take precedence over anything here.

## What normalization is (and is not)

Normalization is a **deterministic transform**: map each source line item to a standard
account, roll the detail up per account and period, apply documented and sourced adjustments,
keep provenance to the source cell, and tie the result back to the source's own subtotals and
the balance-sheet identity. It is **not** an accounting, audit, or investment opinion, and it
never changes the source figures — a mapped/rolled-up value carries provenance so a reviewer
can trace it back to the exact cell.

## Standard account mapping

- Each `mapping` row binds a `(source_label, statement)` to a `std_account` in the standard
  taxonomy, with an optional `normal_sign` (the expected sign of the reported value).
- Detail (non-subtotal) line items are rolled up: `normalized_value = sum(mapped detail) +
  sum(documented adjustments)`. Subtotal lines (`is_subtotal: true`) are **reference control
  totals** used for tie-outs, never rolled into an account (that would double-count).
- A detail line whose `(raw_label, statement)` is not in the mapping is reported under
  `unmapped` and fires `unmapped_line_item` — it is never silently dropped.
- Adjustments are **reclass / non-recurring / normalization** entries only; each must carry a
  `rationale` and `source_ref`, and a material adjustment needs an `approver`.

## Check taxonomy

| Check | Severity | Fires when (default config) | Evidence attached |
| ----- | -------- | --------------------------- | ----------------- |
| `missing_provenance` | medium | A mapped detail line has no `source_ref` (untraceable to a source cell) | The untraceable line rows |
| `unmapped_line_item` | medium | A source detail line has no mapping to a standard account | The unmapped line rows |
| `unexplained_adjustment` | medium | An adjustment lacks `rationale` or `source_ref`, **or** its magnitude ≥ `adjustment_materiality_pct` (default 5%) of revenue with no `approver` | The adjustment rows |
| `subtotal_tie_out_break` | high | A reported subtotal differs from the sum of its declared `components` by more than `tie_out_tolerance` (default 1.0) | Reported vs computed + diff |
| `balance_sheet_identity_break` | high | Normalized total assets ≠ total liabilities + total equity within `tie_out_tolerance` | The three role anchors + imbalance |

Checks are **independent and evaluable-on-data**: a check whose data is absent (e.g.
`balance_sheet_identity_break` when the extract has no `total_assets/liabilities/equity`
role anchors, or `subtotal_tie_out_break` when no subtotal declares `components`) is reported
under `not_evaluable`, never silently passed. There is no opaque composite "quality score".

## Readiness mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Model-ready** | 0 findings fired |
| **Needs mapping review** | ≥ 1 finding fired, all medium severity, and fewer than `escalate_finding_count` (default 4) |
| **Hold - tie-out break** | Any **high**-severity finding fired (a tie-out or identity break), OR ≥ `escalate_finding_count` findings fired |

The readiness band is a **triage suggestion for a human reviewer**. It is not an accounting
sign-off, an audit conclusion, or a statement that the data is fit to book — the reviewer
accepts the mapping and resolves breaks before the dataset is used downstream.

## Hard boundaries (fail closed)

- Never opine that the statements **are** GAAP/IFRS-compliant, materially correct, accurate,
  or "fairly stated" — that is an accounting/audit judgment. Describe the mapping and the
  tie-out evidence; attribute any conclusion to the human reviewer.
- Never issue an **investment, credit, or accounting recommendation** (buy/sell/rating,
  creditworthiness, "good/bad investment") off the normalized figures.
- Never **restate, re-book, or post** figures to the GL, subledger, or any system of record —
  the output is model-ready data with provenance, not a journal or a ledger write.
- Never produce **borrower credit spreading** into a bank credit template — that is a separate
  workflow (`financial-spreading-assistant`).
- Never **tune thresholds** to make a specific extract pass; use only the versioned config.

## Review considerations (always include when any finding fired)

A source subtotal that legitimately includes items outside this extract (capture
completeness), a rounding or presentation-scale difference rather than a true break, an
adjustment pre-approved under a standing normalization-policy delegation, an unmapped line
that is genuinely immaterial or out of model scope, or a source cell whose reference arrives
in a later extract. The pack must invite the reviewer to weigh these before concluding.
