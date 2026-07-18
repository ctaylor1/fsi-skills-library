# Adjacent-Skill Handoffs — policy-document-explainer

This skill produces a **normalized, plain-language policy-element map** and stops. It does not
determine coverage, evaluate a claim, compare policies, or advise. Downstream skills consume
the map via its durable `explanation_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `coverage-gap-analyzer` | User asks whether they have enough coverage or where the gaps are vs. their needs/exposures (analytical, non-advice) | `explanation_id` + normalized element map |
| `claim-readiness-checker` | User is preparing a claim and wants completeness/evidence/deadline checks | `explanation_id` + coverage/condition context |
| `claim-denial-appeal-helper` | A claim was denied and the user wants to understand the denial and draft an appeal | `explanation_id` + cited denial-relevant clauses |
| `premium-quote-comparator` | User wants to compare policies, quotes, premiums, or deductibles | `explanation_id` per policy |
| `policy-wording-comparator` | A professional needs a form/version/wording comparison against filed/approved forms (R3) | `explanation_id` + form edition/citations |

A **specific coverage or claim-outcome question** ("is my flood damage covered?", "will this
claim be paid?") is **not** routed to another explainer — it is a claims/underwriting
decision. Explain the relevant clause neutrally and direct the reader to the insurer/adjuster.

## Upstream (may call this skill)

`coverage-gap-analyzer`, `claim-readiness-checker`, `claim-denial-appeal-helper`, and
`premium-quote-comparator` may request a fresh plain-language element map from this skill
rather than re-parsing the policy themselves.

## Duplicate-execution prevention

- This skill **only explains** the document as written; it must not perform gap analysis,
  claim evaluation, comparison, appeal drafting, or advice — those belong to the skills above.
- Downstream skills must **not** re-parse the policy when a valid `explanation_id` for the same
  policy + effective window already exists; they reuse it.
