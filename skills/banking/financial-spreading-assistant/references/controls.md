# Controls — financial-spreading-assistant

- **Risk tier:** R2 — analytical / model. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — required before the spread is written to the credit
  file / system of record or sent to the borrower. Internal analytical use may be reviewer-sampled.

## Prohibited (fail closed)

- No **credit decision, credit rating, or eligibility determination** — never state or imply the
  borrower is approved, pre-approved, declined, creditworthy, qualifies for a facility/limit, or
  is a good/poor credit.
- No **recommendation** to extend, decline, grant, or price a facility, and no **investment or tax
  advice**.
- No **guessing an ambiguous mapping** — a line with no valid taxonomy code and no map hit is
  escalated to a human, never silently bucketed.
- No **phantom normalization** — a normalized figure may differ from as-reported only by a
  documented, cited add-back.
- No **plugging a tie-out** — if the spread does not balance or reconcile to reported totals,
  surface the gap; never force a balance.
- No **per-borrower tuning** of the taxonomy, ratio formulas, or tolerance — those are versioned
  config.
- No **system-of-record write** — the skill produces a draft artifact only.

## Required output screens (`scripts/validate_output.py`)

- Every period's balance sheet balances: `total_assets == total_liabilities + total_equity`
  (tolerance from `config`, default 1.0).
- Every computed subtotal (`total_assets`/`total_liabilities`/`total_equity`) reconciles to the
  borrower's reported anchor; computed `net_income` ties to reported net income.
- Normalized income statement == as-reported + documented adjustments, per line (no phantom or
  missing add-back).
- Every `adjustments_register` entry carries a non-empty `provenance` **and** `citation`.
- If `ambiguous_mappings` is non-empty, `requires_human_mapping` is true and each entry has a
  citation.
- `spread_id`, `template_version`, `classification_map_version` present (reproducibility).
- No credit-decision / advice language (regex screen over narrative + notes).
- Standing disclaimer present (see below).

## Standing disclaimer

> Spread, ratios, and cash-flow figures are analytical support prepared from borrower-supplied
> documents and analyst-documented adjustments. They are not a credit decision, credit rating,
> eligibility determination, or investment advice, and are not an approval, a denial, or a
> recommendation regarding any facility. Figures depend on the accuracy of the source documents;
> a credit officer must resolve any flagged mappings and make all lending decisions.

## Reproducibility & tie-outs

- `spread_id` + the three versions make every subtotal, ratio, and tie-out reproducible from
  inputs.
- Tie-outs are re-derived by `validate_output` from the spread figures, not trusted from the
  `ok` flags in the pack — a formula-correctness gate.

## Fairness / conduct

- Classify on the financial substance of the line, never on protected-class attributes or proxies.
- Present strained figures plainly; do not soften or overstate. The spread is neutral evidence for
  a human underwriter.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/tax identifiers to the last 4.
- Minimize customer data in the output to what the spread needs.
- Retain the spread + citations + template/classification-map/config versions per records policy;
  log the read and any external-delivery approval. Never exfiltrate borrower data.
