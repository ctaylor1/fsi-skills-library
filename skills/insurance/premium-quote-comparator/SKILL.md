---
name: premium-quote-comparator
description: >-
  Normalize two or more insurance quotes to a common annualized basis and compare them
  side-by-side on premium, fees, deductibles, limits, exclusions, endorsements, and service
  factors, surfacing every material difference that makes the quotes non-like-for-like. Use
  when a consumer, agent, or broker asks "compare these quotes", "which is cheaper and why",
  "normalize these premiums", "what's different between Carrier A and B", or needs a
  reviewer-ready quote comparison from producer/rating data or quote PDFs. This skill
  compares and evidences differences only; it NEVER recommends or selects a policy, gives
  insurance/suitability advice, judges coverage adequacy, or makes a coverage/eligibility
  determination — those are the customer's decision with a licensed producer.
license: MIT
compatibility: Amazon Quick Desktop; requires producer/rating, policy-administration, document-intelligence, and approved-reference/config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Consumer / agent or broker"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Premium Quote Comparator

## Purpose and outcome
Given two or more insurance quotes, **normalize** each to a common 12-month annualized basis,
build a **coverage/limit/deductible comparison grid**, and enumerate every **material
difference** (coverages, deductibles, limits, exclusions, endorsements, term, currency) that
makes the quotes not a like-for-like comparison. A successful output lets a consumer, agent,
or broker see exactly *what differs and by how much* — including that a lower premium usually
reflects a higher deductible, a lower limit, a dropped coverage, or an extra exclusion. The
**decision of which policy to buy remains the customer's**, made with a licensed producer.

## Use when
- "Compare these auto/home/renters quotes for me."
- "Which quote is cheaper, and what am I giving up to get that price?"
- "Normalize these premiums — one is monthly, one is semi-annual, one is annual."
- "What's different between the Carrier A and Carrier B quotes?"
- A producer needs a consistent, cited side-by-side to attach to a client file.

## Do not use
- The user wants a **recommendation** ("which should I buy?", "which is best for me?") →
  out of scope. Present the compared facts and route the choice to the customer/producer.
- The user asks whether a quote's coverage is **adequate for their needs/exposures** →
  `coverage-gap-analyzer`.
- **Policy wording / clause / endorsement** comparison against an approved standard →
  `policy-wording-comparator`.
- **Explain one** policy or quote document in depth → `policy-document-explainer`.
- **Expiring-vs-proposed renewal** review of an in-force policy → `policy-renewal-reviewer`.
- Raw broker emails / ACORD / PDFs that must first be **ingested and structured** →
  `submission-intake-triager`, then return here.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a comparison with a
durable `comparison_id`; downstream adequacy/wording/renewal skills consume it. It must not
duplicate their advice, adequacy judgment, or determination steps.

## Inputs and prerequisites
- **Two or more quotes** for the same risk (a single quote yields nothing to compare — the
  input validator warns).
- Each quote with: `carrier`, `term_months`, `premium{amount, frequency}`, optional
  `fees[]`, and `coverages[{code, name, limit, deductible}]`; optional `exclusions[]`,
  `endorsements[]`, `service_factors{}`, `currency`, `source_ref`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to producer/rating or document-intelligence extraction, and the versioned
  normalization config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **carrier's quote of record**
is authoritative for that carrier's numbers; document intelligence supplies fields when only
a PDF/ACORD is available; reference data/config provide the coverage crosswalk and
normalization multipliers. Cite every figure and difference to its source quote.

## Workflow
1. **Scope & load** — confirm the risk and the set of quotes; load quote fields (or extract
   from documents); validate with `validate_input`. Fail closed on structural errors; heed
   warnings (single quote, mixed currency, mismatched term, uncomparable coverage).
2. **Normalize (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to annualize each
   premium and fee to a 12-month basis and compute the `annualized_total_cost` and
   `cost_spread`.
3. **Build the grid** — union of coverage codes with each quote's `included` / `limit` /
   `deductible`, each cited.
4. **Enumerate differences** — coverage, deductible, limit, exclusion, endorsement, and term
   differences, each naming the affected quotes.
5. **Raise comparability flags** — for every material difference, so the lowest cost is never
   read in isolation. Report the lowest annualized cost as a **fact**, not a suggestion.
6. **Write the comparison** — plain-language side-by-side + the grid + the differences + the
   flags + explicit non-cost factors to weigh (limits, deductibles, exclusions, service
   factors). No recommendation.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every normalized figure is citable; the lowest-cost quote
equals the deterministic argmin; no advice/recommendation/suitability language and no
coverage/eligibility determination is present; the standing disclaimer is included; and
comparability flags are present whenever material differences exist. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the comparison is sent to a customer or
written to a case/system of record. No approval is needed for the reviewer's own read. The
skill never binds, quotes-as-offer, or alters a quote.

## Failure handling
- **Single quote** → state there is nothing to compare; offer to normalize the one quote.
- **Mixed currency** → annualized totals are not directly comparable; flag `currency_mismatch`
  and do not reconcile FX silently.
- **Mismatched term** → premiums are annualized, but limits/exclusions may not be
  term-equivalent; flag `term_mismatch`.
- **Coverage with no limit and no deductible** → mark it not comparable; do not guess.
- **Conflicting extracted vs rated value** → cite both; do not resolve silently.
- **Tool timeout** → return the quotes normalized so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — risk type, quote count, annualized total cost per quote, `cost_spread`, and
   the lowest-cost quote id (as a fact).
2. **Comparison grid** — per coverage code: each quote's included/limit/deductible, cited.
3. **Differences** — coverage / deductible / limit / exclusion / endorsement / term, each
   naming the affected quotes.
4. **Comparability flags** — why the cheapest is not automatically like-for-like.
5. **Machine-readable** — normalized quotes + grid + differences + `comparison_id`.
6. **Standing disclaimer** — "Comparison of quotes only; not insurance advice, a coverage
   determination, or a recommendation to purchase. Coverage selection is the customer's
   decision, made with a licensed producer."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Minimize customer identifiers to what the comparison needs; mask where a
carrier quote carries applicant identifiers not required for the comparison. Retain the
comparison + citations + `config_version` per records policy; log the read and any
external-delivery approval. Never exfiltrate customer or carrier data.

## Gotchas
- **Cheaper is not equivalent.** A lower premium almost always buys a higher deductible, a
  lower limit, a dropped coverage, or an extra exclusion — the comparability flags exist to
  make that trade explicit, never to endorse the cheap quote.
- **Installment loading**: `monthly × 12` can exceed a pay-in-full annual premium; the
  comparison normalizes payment schedules, not the pay-in-full price.
- **`null` limit ≠ unlimited**: a missing limit means the coverage is not included; do not
  read it as "unlimited coverage".
- **Service factors are context, not score**: AM Best / NAIC complaint index are shown to
  inform the reader, never weighted into a ranking.
- **Quotes expire**: a comparison is valid only for its quotes' effective dates; re-rate
  before relying on stale figures.
- **Comparing is not advising**: identifying the lowest cost is factual; telling the customer
  which to buy, or that a policy "is right for you", crosses into advice and is prohibited.
