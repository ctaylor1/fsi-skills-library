# Controls — premium-quote-comparator

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the comparison goes to a customer
  or is written to a case/system of record.

## Prohibited (fail closed)

- No **recommendation, selection, or ranking-as-advice** — never tell the customer which
  quote to buy, which is "best/right for you", or which to drop. The lowest annualized cost
  is reported as a **fact**, never as a suggestion.
- No **insurance / suitability advice** and no **personalized financial advice**.
- No **coverage or eligibility determination** — never state that a person "is covered", "is
  eligible", "qualifies", or that "the claim will be paid". Coverage/eligibility is decided
  by the carrier/underwriter, not this skill.
- No **binding, quoting-as-offer, or price negotiation**; the skill compares existing quotes,
  it does not create or alter them.
- No **silent reconciliation** of non-like-for-like quotes (different currency, term, limits,
  deductibles, coverages) — differences are surfaced as flags.

## Required output screens (`scripts/validate_output.py`)

- Every normalized quote figure is **citable** to its source quote.
- `lowest_annualized_total_cost_quote_id` equals the deterministic argmin over the normalized
  quotes (factual tie-out; no invented "winner").
- No advice/recommendation/suitability language (regex screen: "we recommend", "you should
  buy/choose/select", "the best policy/option/value", "right coverage for you",
  "suitable for you", etc.).
- No coverage/eligibility determination language (regex screen: "you are covered", "you
  qualify", "eligible for coverage", "the claim will be paid", etc.).
- Standing disclaimer present (see below).
- When material differences exist, **comparability_flags** are present so cost is never shown
  without its caveats.

## Standing disclaimer (verbatim)

> Comparison of quotes only; not insurance advice, a coverage determination, or a
> recommendation to purchase. Coverage selection is the customer's decision, made with a
> licensed producer.

## Conduct / fairness

- Compare on quoted terms only; do not infer or use protected-class attributes or proxies.
- Describe differences factually and neutrally; do not disparage a carrier.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Minimize customer PII to what the comparison
  needs; carrier quotes may contain the applicant's identifiers — mask where not required.
- Retain the comparison + citations + `config_version` per records policy; log the read and
  any external-delivery approval.

## Reproducibility

`comparison_id` binds the output to the exact quotes, `as_of` dates, and **config version**;
re-running with the same inputs and config reproduces the normalized figures and differences.
