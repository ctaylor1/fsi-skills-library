# Controls — collections-treatment-planner

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a collections/hardship specialist must adjudicate and
  authorize before any treatment is offered, any outreach is initiated, or any system of
  record is changed.

## Prohibited (fail closed)

- No **regulated decision**: do not approve/deny a treatment, grant forbearance, modify a
  loan, waive/write-off a balance, or agree a settlement.
- No **case closure**, **charge-off**, **re-aging**, **filing** (suit/legal referral), or
  **credit-bureau reporting** — these are human/authorized-system actions.
- No **system-of-record write** and no **setting up** of a payment plan/arrangement; this
  skill recommends, it does not act.
- No **FDCPA/UDAAP-prohibited conduct**: no threats (sue, arrest, wage garnishment, seizure),
  no harassment, no false/misleading statements, no contact that breaches a suppression flag
  or the contact-frequency presumption.
- No **personalized financial/credit advice** and no **affordability determination** — the
  affordability figure is indicative only.

## Required output screens (`scripts/validate_output.py`)

- `requires_human_adjudication` is `true` and the standing human-adjudication disclaimer is
  present.
- Every **eligible** treatment carries ≥ 1 cited evidence row (delinquency basis + policy rule).
- `recommended_treatments` equals exactly the deterministic eligible set (tie-out to the
  engine — no injected or ineligible option).
- No regulated-decision language (regex screen), covering **both** an approval-side commitment
  ("we approve", "approved", "forbearance granted", "closed the case", "charged off", "we have
  filed", "filed suit", "reported to the credit bureau", "settlement is agreed", etc.) **and** a
  denial-side adverse decision — denying/declining/rejecting a forbearance, modification,
  hardship accommodation, arrangement, or request ("the forbearance request is denied", "we
  declined the modification", "rejecting the payment arrangement", etc.). The skill recommends;
  a human adjudicates and issues any approval **or** denial.
- No threat/conduct language ("we will sue you", "garnish your wages", "you will be arrested").
- **Suppression honored:** if outreach is suppressed, no channel may be eligible.
- **Call cap honored:** `phone` may be eligible only when `phone_outreach_eligible` is true.

## Fairness / conduct

- Enhanced-care handling when a vulnerability indicator is present: prefer forbearance /
  affordability-based options over escalation; route to a specialist.
- Do not treat disclosed hardship or a protected-class attribute (or a proxy) as an adverse
  input; do not use it to justify harsher treatment. Describe circumstances factually and
  without stigmatizing language.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4.
- Minimize customer data to what evidences an eligibility decision.
- Retain the plan + citations + `config_version` per records policy; log the read and the
  specialist's adjudication/authorization.

## Reproducibility

`plan_id` binds the output to the exact case inputs, `as_of`, and **config version**;
re-running with the same inputs and config reproduces the bands, screens, and eligible set.
