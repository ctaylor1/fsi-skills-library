# Controls — financial-goal-progress-analyzer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a licensed human advisor must adjudicate before any
  recommendation, suitability conclusion, client commitment, trade, filing, posting, closure,
  or system-of-record change. The skill stages none of these.

## Prohibited (fail closed)

- No **recommendation** or **product/allocation/security selection** ("we recommend", "buy the
  fund", "sell the position", "you should …").
- No **suitability determination** or sign-off ("is suitable", "suitability approved").
- No **personalized investment, tax, or legal advice**.
- No **guarantee** of results ("guaranteed to reach", "will achieve the goal"); projections are
  estimates only.
- No **trade / filing / posting / closure / account write** ("place/execute the trade", "file",
  "post the journal", "close the goal/account").
- No **tuning of approved assumptions to the individual** to make a goal "look" on track; use
  only the versioned assumptions.

## Required output screens (`scripts/validate_output.py`)

- Every evaluated goal has a status band and >= 1 cited evidence row.
- Each goal's status equals the deterministic band mapping from its funded ratio.
- `summary.status_counts` ties to the per-goal bands.
- Any goal not "On track" carries illustrative levers.
- No recommendation / suitability / advice / guarantee / trade / filing / closure language in
  the narrative or notes (regex screen).
- Standing disclaimer present: "Decision-support analysis only under approved assumptions; not
  a recommendation, suitability determination, guarantee of results, or investment/tax advice.
  No decision, trade, filing, or system-of-record change has been made."

## Fairness / conduct

- Present projections and gaps factually; avoid pressure or urgency language toward the client.
- Do not use protected-class attributes or proxies in any status logic.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/client numbers to last 4.
- Minimize customer data to what evidences a goal's status.
- Retain analysis + citations + assumptions version per records policy; log read + approval.

## Reproducibility

`analysis_id` binds the output to the exact inputs, as-of date, and **assumptions version**;
re-running with the same inputs and assumptions reproduces the projections, funded ratios, and
status bands.
