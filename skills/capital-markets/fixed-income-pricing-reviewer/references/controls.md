# Controls — fixed-income-pricing-reviewer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the pack goes to a case / system of
  record (IPV queue, price-challenge log) or onward to another team.

## Prohibited (fail closed)

- No **valuation determination** or statement/implication that a mark **is** correct, accurate,
  "fair value", a "mismark", or "confirmed mispricing".
- No **price approval, override, restatement, or booking** of a mark, and no recommendation to
  do any of these.
- No **IPV / price-verification sign-off**, and no waiving/clearing/dismissing of a pricing
  exception.
- No **conduct determination** (e.g., asserting a trader marked to hit a P&L target) — route to
  surveillance and a human.
- No **threshold tuning to a desk/trader**; use only the versioned config.
- No **opaque pricing score** presented as decisive; checks are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every flagged check has ≥1 cited evidence row.
- Each instrument's `suggested_priority` equals the deterministic band mapping from its flagged
  set; `overall_suggested_priority` equals the highest instrument band.
- No determination/approval/mark-action language in the narrative, notes, or any check reason
  (regex screen: "approve the mark", "override approved", "book the price", "mark is fair value",
  "sign off IPV", "restate the mark", "this is a mismark", "confirmed mispricing", etc.).
- Standing disclaimer present: "Pricing-review evidence only; not a valuation determination or
  price approval. No mark has been changed, approved, or booked."
- Benign-explanation prompts included when any check flagged.

## Conduct / fairness

- Describe pricing patterns factually; never attribute intent or motive to a trader or desk.
- Do not let a desk's or trader's identity influence the checks or thresholds.

## Data classification, privacy, records

- **Highly Confidential.** Treat embedded account/holder identifiers as NPI/PII; mask instrument
  identifiers to the last 4.
- Minimize data in the output to what evidences a flagged check.
- Retain review + citations + `config_version` per records policy; log read + external-delivery
  approval.

## Reproducibility

`review_id` binds the output to the exact inputs, focal instruments, as-of date, and **config
version**; re-running with the same inputs and config reproduces the checks and priority bands.
