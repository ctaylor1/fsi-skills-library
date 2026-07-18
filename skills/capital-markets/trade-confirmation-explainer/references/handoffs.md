# Adjacent-Skill Handoffs — trade-confirmation-explainer

This skill produces a **plain-language explanation of one trade confirmation** and stops. It
does not judge, dispute, resolve, or act. Downstream skills consume its normalized explanation
object via the durable `explanation_id`.

## Downstream (this skill hands off to)

| Downstream skill | When to route | Handoff artifact |
| ---------------- | ------------- | ---------------- |
| `trade-break-resolver` | The customer or ops believes the confirmation is wrong, or it disagrees with the clearing record (a break) | `explanation_id` + both cited figures |
| `best-execution-reviewer` | Question about whether the execution price/venue met best-execution obligations | `explanation_id` + execution context |
| `communications-compliance-reviewer` | The explanation will be sent to a client and needs supervised-comms review before delivery | `explanation_id` + draft narrative |
| `corporate-action-interpreter` | The "trade" is actually a corporate-action-driven booking (e.g. tender, exchange) needing interpretation | confirmation reference |
| `prospectus-plain-language-breakdown` | User pivots from the confirmation to understanding the security/offering itself | instrument identifier |

For personalized suitability or "was this a good trade" questions, there is **no in-scope
skill** — that is investment advice; decline and direct the user to a licensed representative.

## Upstream (may call this skill)

`communications-compliance-reviewer` and client-servicing workflows may request a plain-language
confirmation explanation rather than drafting one by hand.

## Duplicate-execution prevention

- This skill **only explains**; it must not resolve breaks, judge best execution, assess
  suitability, or draft client correspondence for delivery — those belong to the skills above.
- Downstream skills must **not** re-derive the confirmation figures when a valid
  `explanation_id` for the same confirmation already exists; they reuse it.
