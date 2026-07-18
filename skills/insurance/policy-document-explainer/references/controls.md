# Controls — policy-document-explainer

- **Risk tier:** R1 — informational. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the explanation is delivered to a
  customer or written to a system of record; not required for the user's own read.

## Prohibited (fail closed rather than do these)

- No **coverage determination**: never state that a specific loss, claim, incident, or the
  reader is or is not covered, or that a claim would be paid, approved, or denied. That is a
  claims/underwriting decision, not an explanation.
- No **eligibility determination**: never state that the reader qualifies / does not qualify /
  is or is not eligible.
- No **claim-outcome prediction** for a described situation.
- No **advice**: never tell the reader to buy, drop, switch, keep, add, increase, or reduce
  coverage; no "better/best policy", "under-/over-insured", "too much/too little coverage";
  no insurance, legal, or tax advice.
- No **wording invention** for unreadable/missing sections; no **merging** of multiple
  policies or editions without explicit user confirmation.
- No **overriding** the policy of record with a user assertion.

## Required "no-determination / no-advice" language screen

`scripts/validate_output.py` scans the narrative, element summaries, and notes for
coverage-determination, eligibility, claim-decision, and advice/recommendation phrasing
(e.g. "you are covered", "your claim will be approved/denied", "we will pay", "you qualify",
"we recommend", "you should buy/drop/switch", "under-insured", "better policy",
"legal/financial/tax advice"). Any hit **fails closed**. Neutral third-person description of
what the document says (e.g. "Section I excludes flood") is permitted and expected.

A standing disclaimer must be present: "Informational explanation only; not a coverage
determination, claim decision, or insurance/legal advice."

## Deterministic internal-consistency checks

- Every explained element carries a **non-empty citation**.
- Each element's `element_type` is a recognized policy-element type.
- `sections_explained_count` **ties** to the number of `elements` listed (no silent
  over/under-count).

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)**.
- Mask policy/account numbers to last 4 and redact insured identifying details in all output.
  Keep the policy and explanation within the approved environment; never exfiltrate.
- Retain the explanation + citations per records policy. Log: source read, `explanation_id`
  creation, and any external-delivery approval (who/when).

## Reproducibility

Given the same policy document and effective window, the explanation must be reproducible:
the `explanation_id` binds the output to the exact inputs and citations used.
