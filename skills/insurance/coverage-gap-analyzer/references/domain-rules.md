# Domain Rules — coverage-gap-analyzer

Explainable coverage **gaps** and how they map to a **review-priority band**. Thresholds are
configuration (versioned, owned by the underwriting-rules team), not hard-coded judgments,
and never tuned to an individual. The **policy of record** and applicable filed forms take
precedence; stated exposures are client-provided and unverified.

## Gap taxonomy

| Gap | Fires when (default config) | Evidence attached |
| --- | --------------------------- | ----------------- |
| `missing_coverage` | An exposure names a `required_coverage` with **no** matching coverage `type` in the policy schedule | Exposure + coverage-schedule citation |
| `exclusion_match` | An exposure `peril` is named in a policy **exclusion** and **no** endorsement buys it back | Exposure + exclusion citation |
| `limit_shortfall` | Exposure `value` exceeds the matching coverage `limit` (by more than `limit_shortfall_tolerance`, default 0) | Exposure + coverage citation + shortfall |
| `sublimit_shortfall` | Exposure `value` exceeds the applicable category `sublimit` (e.g., jewelry) even if the aggregate limit is adequate | Exposure + coverage citation + shortfall |
| `coinsurance_shortfall` | Carried `limit` is below `coinsurance` × replacement `value` (penalty exposure) | Exposure + coverage citation + required limit |
| `deductible_burden` | Coverage `deductible` exceeds `deductible_burden_ratio` (default 0.10) of the exposure `value` — informational | Exposure + coverage citation + share |
| `endorsement_gap` | An exposure names a `recommended_endorsement` that is **not** attached to the policy | Exposure + coverage-schedule citation |

Gaps are **additive and independent**; the output reports each that fired with its own
evidence and dual citation. A gap type with no data to evaluate is reported under
`not_evaluable` (e.g., no coverage declares a coinsurance clause). There is no opaque
composite "coverage score".

## Priority mapping (deterministic, documented)

Let `escalators = {missing_coverage, exclusion_match}`.

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 gaps fired |
| **Review** | 1–2 gaps fired and none is an escalator |
| **Elevated** | ≥ 3 gaps fired, OR any escalator (`missing_coverage` / `exclusion_match`) fired |

Priority is a **triage suggestion for a licensed insurance professional**. It is not a
coverage determination and it never binds, quotes, or recommends a transaction.

## Hard boundaries (fail closed)

- Never state or imply that a claim/loss **is / is not / will be** covered, paid, denied, or
  eligible — describe the gap factually and attribute any conclusion to the licensed professional.
- Never conclude coverage is **adequate / sufficient / right for the customer**; report the
  measured shortfall only.
- Never recommend a **transaction** (buy, drop, cancel, switch, change a limit) or give
  personalized insurance/legal/tax advice.
- Never tune thresholds to the individual or infer "what's right for this person" beyond the
  computed gap.

## Review prompts (always include when any gap fired)

Replacement cost vs. actual-cash-value basis; other policies that may already cover the
exposure (umbrella, standalone/NFIP flood, scheduled personal-articles, auto); an intentional
high deductible or lower limit chosen for premium; blanket/agreed-value/extended-replacement
provisions; statutory, lender, or lease minimums. The analysis must invite the professional
to weigh these before acting.
