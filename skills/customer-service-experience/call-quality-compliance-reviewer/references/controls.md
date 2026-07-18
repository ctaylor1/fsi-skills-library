# Controls — call-quality-compliance-reviewer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the scorecard is delivered to an
  agent, team lead, calibration/system of record, and before any coaching or routing.

## Prohibited (fail closed)

- No **agent-misconduct determination** or statement/implication that the agent **committed**
  misconduct, a **regulatory breach**, or a **reportable breach** (intent/adjudication).
- No **pass/fail or scoring presented as decisive**, and no **disciplinary/HR action**
  (warning, termination, "fail the agent") — those belong to the human QA/HR process.
- No **regulatory report filed** or recommendation to file/report to a regulator — route to
  the compliance officer / licensed specialist.
- No **personalized advice** (telling a customer to buy/sell/invest) inferred from the review.
- No **rubric tuning to the individual** agent or customer; use only the versioned config.
- No **opaque scoring** presented as decisive; findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥1 cited evidence row (a turn, or the scanned scope for an absence).
- No determination/action/advice language (regex screen: "confirmed misconduct", "committed
  a regulatory/compliance breach", "reportable breach", "must be terminated", "disciplinary
  action", "fail the agent", "report the breach to the regulator", "recommend you buy/sell",
  etc.).
- Suggested disposition equals the deterministic mapping from the fired findings' severities
  (any critical → Compliance review required; else any coaching → Coaching recommended; else
  Meets expectations).
- Standing disclaimer present: "Quality-review evidence only; not a determination of
  misconduct, a regulatory breach, or a disciplinary decision. No action has been taken."
- Considerations (benign-explanation prompts) included when any finding fired.

## Fairness / conduct

- Never use protected-class attributes or proxies as a quality signal.
- Vulnerability cues drive **accommodation/referral**, never an adverse conclusion about the
  customer or a diagnostic label.
- Describe agent behavior factually; avoid stigmatizing language. Treat agent-performance
  data as confidential.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Operate on de-identified transcripts; mask any
  account/card numbers to last 4.
- Minimize customer data to what evidences a finding.
- Retain scorecard + citations + rubric version per records policy; log read + approval.

## Reproducibility

`review_id` binds output to the exact transcript, context, and **rubric config version**;
re-running with the same inputs and config reproduces the findings and the disposition.
