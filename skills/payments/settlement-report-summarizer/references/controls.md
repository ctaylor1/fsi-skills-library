# Controls — settlement-report-summarizer

- **Risk tier:** R1 — informational. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the summary is delivered to a
  merchant/counterparty or written to a system of record; not required for the user's own read.

## Prohibited (fail closed rather than do these)

- No **fee-optimization, financial, tax, or accounting advice**; no opinion that fees, rates,
  markup, or reserves are high/low/excessive/reasonable, and no suggestion to switch,
  negotiate, renegotiate, shop, dispute, or change processors (that is advice; route elsewhere).
- No **reconciliation determination** or confirmation that the settlement is correct — the
  skill does not assert the payout "reconciles", "ties out to your ledger/bank", "matches your
  records", or that there are "no discrepancies/breaks" (that is a control decision; route to
  the reconciliation/exception skills).
- No **chargeback or dispute determination** (whether a chargeback is valid, winnable, or
  recoverable).
- No **amount invention** for unvalued/pending lines; no **merging** of multiple settlement
  batches or funding dates without explicit confirmation.
- No **overriding** the processor's settlement of record with a merchant assertion.

## Required "no-advice / no-determination" language screen

`scripts/validate_output.py` scans the narrative/notes for two families of phrasing and
**fails closed** on any hit:

1. **Advice / optimization** — recommend, you should/could, should switch/renegotiate,
   too high, fees are excessive/competitive, better rate/deal, switch processors, negotiate,
   overcharged, shop around.
2. **Settlement determination** — reconcile(s/d), ties out to your…, matches your
   ledger/books/bank, settlement is correct/accurate/verified, confirmed/verified correct,
   no discrepancies/breaks, deposit/funding is confirmed.

A standing disclaimer must be present: *"Informational summary only; not financial, tax, or
fee-optimization advice, and not a settlement reconciliation, dispute assessment, or
confirmation that the settlement is correct."* The disclaimer field is excluded from the
language scan (it names the boundary rather than crossing it).

## Deterministic tie-outs (also enforced by `validate_output.py`)

- **Gross-to-net:** `sum(signed category amounts) == net_settlement`.
- **Funding:** `net_settlement == funding.expected_net` when funding is present.
- **Fees:** `total_fees == sum(|fee categories|)`; `effective_fee_rate_pct == total_fees /
  gross_sales * 100`.
- **Brand split:** `by_card_brand` values tie to `gross_sales`.
Any untied figure fails closed — do not present an untied summary.

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII; cardholder data)**. Never emit a
  full PAN; card data is limited to brand and, at most, last 4. Mask merchant and bank
  account numbers to last 4.
- Keep settlement data within the approved environment; never exfiltrate. Retain the snapshot
  + citations per records policy. Log: source read, snapshot creation, and any
  external-delivery approval (who/when).

## Reproducibility

Given the same settlement report and as-of date, the summary must be reproducible: the
`snapshot_id` binds the output to the exact inputs and citations used.
