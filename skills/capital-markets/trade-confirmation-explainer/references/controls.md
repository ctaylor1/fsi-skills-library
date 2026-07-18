# Controls — trade-confirmation-explainer

- **Risk tier:** R1 — informational. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the explanation is delivered to a
  client or written to a system of record; not required for the user's own read.

## Prohibited (fail closed rather than do these)

- No investment **advice, recommendation, or opinion** — whether the trade, price, timing, or
  security was good/bad, or what to do next (buy/sell/hold/switch).
- No **judgment about the charges** — "the commission is too high", "you overpaid", "you got a
  better/worse price", "this markup is excessive". Explaining what a charge *is* and its amount
  is in scope; grading it is not.
- No **fairness / best-execution / suitability determination**, and no **error or fraud
  finding** ("this confirmation is wrong", "you were overcharged"). Route disputes and
  best-ex/suitability questions to the adjacent skills in `handoffs.md`.
- No **inventing or altering** disclosed figures; no **overriding** the books-and-records
  confirmation with a user assertion; no **merging** multiple confirmations into one.

## Required "no-advice" language screen

`scripts/validate_output.py` scans the narrative/notes for advice, recommendation, and
value-judgment phrasing (recommend / you should / good-bad-fair price or trade / too high /
overpaid / better price / switch brokers / dispute the charge, etc.). Any hit **fails closed**.
A standing disclaimer must be present:
"Informational explanation only; not investment advice or a recommendation."

## Deterministic money tie-out

`scripts/calculate_or_transform.py` and `scripts/validate_output.py` reproduce the
confirmation's arithmetic (principal from quantity×price×price_factor; net_amount from
principal ± charges + accrued interest) so the explanation cannot silently misstate a number.
A tie-out miss **fails closed** — the numbers are re-checked or the gap is surfaced, never
smoothed over. See [domain-rules.md](domain-rules.md) for the canonical formula.

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)**.
- Mask account numbers to last 4 in all output. Keep confirmation data within the approved
  environment; never exfiltrate.
- Retain the explanation + citations per records policy. Log: source read, explanation
  creation, and any external-delivery approval (who/when).

## Reproducibility

Given the same confirmation source, the explanation must be reproducible: the
`explanation_id` binds the output to the exact confirmation and citations used.
