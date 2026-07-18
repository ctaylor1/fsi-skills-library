# Controls — margin-collateral-optimizer

- **Risk tier:** R2 — analytical/drafting support. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — treasury **and** operations approval required
  before the recommendation is delivered as an instruction or written to a system of record.
  Internal analytical use may be reviewer-sampled.

## Prohibited (fail closed)

- No **pledging, posting, moving, substituting, or settling** collateral, and no staging of
  any such instruction — the skill recommends; treasury and operations decide and execute.
- No **disputing, accepting, or rejecting** a margin call on the firm's behalf.
- No **binding funding decision** (borrow/lend, repo, FX to raise cash) and no **personalized
  investment advice** or guaranteed-return claim.
- No **silent shortfall**: an under-covered call or a concentration-limit breach must be
  surfaced in `unresolved_items`, never hidden or auto-resolved.
- No **eligibility or haircut override** beyond the versioned schedule; no tuning limits to a
  desired outcome.

## Required output screens (`scripts/validate_output.py`)

- Every allocation line carries a non-empty **source citation** (inventory row + haircut
  entry).
- **Coverage math ties out** per call: line `post_haircut_value == posted_market_value *
  (1 - haircut)`; lines sum to `total_post_haircut_value`; `coverage_ratio` and `shortfall`
  are consistent with `required_amount`.
- **Surfacing:** any call with a shortfall or a concentration breach appears in
  `unresolved_items`.
- **No prohibited language** (regex screen: "we have pledged", "moved the collateral",
  "execute the substitution", "disputed the margin call", "no approval is needed",
  "guaranteed return", "you should buy/sell", etc.).
- **Standing disclaimer** present.
- `approval_required` is **true**.

## Market conduct

- Treat the CSA / clearing rulebook, funding curve, and limit config as **versioned
  contracts**; do not infer terms not in the schedule.
- Describe the funding-cost estimate as an **estimate**, not a promise; it is an input to a
  human decision, not advice to trade.
- Do not use the recommendation to front-run, time, or advantage the firm against the
  counterparty; the output is an internal operational aid.

## Data classification, privacy, records

- **Highly Confidential.** Positions, counterparties, and agreements are sensitive; minimize
  to what the recommendation requires and mask account identifiers where shown.
- Retain the recommendation + citations + `config_version` per records policy; log the read
  and any external-delivery approval.

## Reproducibility

`recommendation_id` binds the output to the exact inputs, `as_of`, and **config version**;
re-running with the same inputs, schedule, and limits reproduces the allocation, coverage,
and funding-cost estimate.
