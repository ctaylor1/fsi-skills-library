# Controls — account-anomaly-screener

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the pack goes to a customer or a
  case/system of record.

## Prohibited (fail closed)

- No **fraud/AML determination** or statement/implication that activity **is** fraud,
  laundering, or "structuring to evade" (intent).
- No **account action** or recommendation to act: block, freeze, hold, close, reverse,
  restrict, or contact-for-verification-as-instruction.
- No **filing** (dispute, SAR) — route to the appropriate draft-only skill and human.
- No **threshold tuning to the individual**; use only the versioned config.
- No **opaque scoring** presented as decisive; signals are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired signal has ≥1 cited evidence row and a named baseline.
- No determination/action language (regex screen: "is fraud", "fraudulent", "block the
  account", "freeze", "structuring to evade", "we should file", "confirmed fraud", etc.).
- Suggested priority equals the deterministic mapping from the fired-signal set.
- Standing disclaimer present: "Screening evidence only; not a fraud determination. No
  account action has been taken."
- Benign-explanation prompts included when any signal fired.

## Fairness / conduct

- Do not use protected-class attributes or proxies as signals.
- Describe patterns factually; avoid stigmatizing language about the customer.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/card numbers to last 4.
- Minimize customer data to what evidences a fired signal.
- Retain screening + citations + config version per records policy; log read + approval.

## Reproducibility

`screening_id` binds output to the exact inputs, baseline window, and **config version**;
re-running with the same inputs and config reproduces the signals and priority.
