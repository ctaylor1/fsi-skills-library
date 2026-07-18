# Controls — commercial-cash-management-advisor

- **Risk tier:** R2 — analytical / domain workflow. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the advisory goes to the client
  or a CRM/system of record.

## Prohibited (fail closed)

- No **binding product or pricing decision** — no rate, ECR, fee, or "final pricing"
  commitment; no signed proposal or "locked-in" quote.
- No **credit decision** — never approve/decline or imply approval of a working-capital line,
  overdraft facility, or loan; never assess or assert creditworthiness. Route to lending.
- No **personalized investment advice** — never recommend a specific security or assert a
  return/yield; route sweep/investment suitability to a licensed specialist.
- No **system-of-record action** — never open, enroll, change, close, or price an account or
  service; that is treasury operations under authorization.
- No **guarantee** of savings, return, or outcome; no threshold tuning to make a client
  "qualify".
- No **opaque scoring** presented as decisive; recommendations are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every recommended service has ≥1 cited evidence row **and** ≥1 implementation question.
- Suggested engagement priority equals the deterministic mapping from the recommended set.
- No binding-decision/advice language (regex screen: "you are approved", "approved for a
  line/overdraft", "guaranteed savings", "we guarantee", "final pricing", "locked-in rate",
  "we commit to", "binding offer", "as your financial advisor", "you should invest",
  "we have opened", "enroll you in", etc.).
- Standing disclaimer present: "Advisory analysis only; not a binding product, pricing,
  credit, or investment decision. No account or service has been opened, changed, or priced."

## Fairness / conduct

- Recommend on documented cash-flow fit only; never on protected-class attributes or proxies.
- Present recommendations as options for the client, not pressure; state that fit is a
  starting point, not an offer.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4.
- Minimize customer data to what evidences a recommendation.
- Retain advisory + citations + config version per records policy; log read + approval.

## Reproducibility

`advisory_id` binds the output to the exact inputs, analysis period, and **config version**;
re-running with the same inputs and config reproduces the recommendations and priority.
