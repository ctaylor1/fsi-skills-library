# Controls — portfolio-proposal-comparator

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a licensed human must adjudicate before the comparison is used for
  any client-facing recommendation, suitability/Reg BI determination, trade, or system-of-record write.

## Prohibited (fail closed)

- No **selection, ranking, or recommendation** of a proposal (no "best/right/suitable/preferred
  proposal", no "we recommend", no "you should choose"). The comparator surfaces differences only.
- No **suitability or Reg BI determination** ("is suitable", "suitability met/approved"); route the
  suitability documentation to `suitability-reg-bi-reviewer` and the decision to the licensed advisor.
- No **personalized investment or tax advice** ("should buy/sell", "our advice is", "realize this
  gain"). The tax-drag figure is an approved-assumption estimate, explicitly not tax advice.
- No **trade, order, rebalance, filing, or system-of-record write**, and no recommendation to execute
  one — those are human / authorized-system actions.
- No **threshold tuning to the individual proposal or client**; use only the versioned config.
- No **outcome guarantee** or forecast dressed as certainty; risk is stated allocation/concentration.

## Required output screens (`scripts/validate_output.py`)

- Each proposal's `total_cost_bps` ties out to `expense_weighted_bps + advisory_fee_bps`.
- Every flag has ≥ 1 cited evidence row.
- The `assumptions` block is present and non-empty (transparent assumptions).
- `adjudication_required` is `true` (mandatory human adjudication).
- No proposal-selection field carries a value (`recommended_proposal`, `selected_proposal`, `winner`,
  `preferred_proposal`, `suitable_proposal`, `best_proposal`, `chosen_proposal`).
- No decision / recommendation / advice / trade-execution / filing language (regex screen).
- Standing disclaimer present: "Comparison and evidence only; not investment, tax, or suitability
  advice and not a recommendation to select any proposal. A licensed human must review before any
  client discussion or action; no trade has been placed and no system of record has been updated."

## Fairness / conduct

- Present proposals **symmetrically**; do not lead with the cheaper/simpler option.
- Describe conflicts (proprietary product, revenue-sharing, share-class) factually; disclose, do not
  net them away or minimize them.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask client/account numbers to last 4.
- Minimize customer data to what evidences a difference or flag.
- Retain the comparison + citations + config version per records policy; log read + adjudication/
  delivery approval.

## Reproducibility

`comparison_id` binds the output to the exact proposals, as-of snapshot, and **config version**;
re-running with the same inputs and config reproduces the metrics, flags, and matrix.
