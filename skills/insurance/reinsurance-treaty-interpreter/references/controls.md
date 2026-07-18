# Controls — reinsurance-treaty-interpreter

- **Risk tier:** R2 — analytical / interpretive. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the interpretation is delivered
  externally (cedent, broker, reinsurer) or written to a system of record; not required for the
  analyst's own read. A binding recoverability decision always belongs to the authorized
  ceded-claims function, never this skill.

## Prohibited (fail closed rather than do these)

- No **coverage or recoverability determination** on a specific claim — whether a loss is (or
  would be) recoverable, covered, excluded, or payable, or how much the reinsurer "will pay".
  Interpreting what a clause *says* and illustrating the layer arithmetic is in scope;
  determining an actual claim outcome is not.
- No **advice or opinion** on what to do — bill, collect, commute, dispute, accept, deny,
  reserve, or book a recoverable — and no legal, actuarial, or accounting advice.
- No **reserving, IBNR, or accounting** conclusion; no **wording-adequacy or dispute** opinion.
- No **inventing or altering** treaty terms; no **overriding** the treaty of record with a user
  assertion; no **merging** of multiple treaties, layers, or periods.

## Required "no-advice" language screen

`scripts/validate_output.py` scans the narrative, clause summaries, and notes for
determination and advice phrasing (this loss is recoverable/covered/excluded; the reinsurer
will/must pay/reimburse/indemnify; you are entitled to recover; you should bill/collect/
commute/reserve/book/deny; we recommend/advise; legal/actuarial/accounting advice, etc.). Any
hit **fails closed**. Neutral third-person interpretation of the wording, and figures labeled
**illustrative**, are permitted. A standing disclaimer must be present: "Informational
interpretation only; not a coverage or recoverability determination, reserving or accounting
decision, or legal advice."

## Deterministic recovery tie-out

`scripts/calculate_or_transform.py` computes, and `scripts/validate_output.py` re-checks, the
layer arithmetic (per-occurrence layer loss = `min(max(gross − attachment, 0), limit)`; ceded
capped by the remaining aggregate; cumulative erosion; reinstated amount and reinstatement
premium) so the illustration cannot silently misstate a figure. A tie-out miss **fails
closed** — the numbers are re-checked or the gap is surfaced, never smoothed over. See
[domain-rules.md](domain-rules.md) for the canonical formulas.

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)**.
- Mask treaty, account, and policy numbers to last 4, and any claimant/insured identifying
  details in loss data. Keep treaty and loss data within the approved environment; never
  exfiltrate.
- Retain the interpretation + citations per records policy. Log: source read, interpretation
  creation, and any external-delivery approval (who/when).

## Reproducibility

Given the same treaty source, period, and loss data, the interpretation must be reproducible:
the `interpretation_id` binds the output to the exact treaty, clauses, and citations used.
