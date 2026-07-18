# Adjacent-Skill Handoffs — fixed-income-pricing-reviewer

This skill produces a cited **pricing-review pack** (`review_id`) and stops. It does not
challenge, approve, override, restate, book, sign off, or dispose of a mark.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `valuation-reviewer` | The exception needs a broader valuation-method / hierarchy / IPV-governance review (methods, inputs, uncertainty, overrides) | `review_id` + flagged instruments |
| `model-validation-assistant` | The pricing model or curve methodology itself needs independent validation | `review_id` + instrument + model reference |
| `surveillance-alert-triager` | The mark pattern suggests possible manipulation/misconduct and needs triage before investigation | `review_id` + evidence |
| `market-surveillance-alert-investigator` | An escalated surveillance case needs deep order/trade/message evidence | `review_id` + evidence |
| `communications-compliance-reviewer` | Trader communications around the mark need review | `review_id` + context |
| `trade-confirmation-explainer` | The user actually wants a confirmation explained, not a pricing-exception review | instrument + confirmation |

## Human / operations handoff (no catalog skill owns these)

The **price challenge, the price override/approval, the IPV sign-off, and the booked or restated
mark** belong to the human valuation-control / independent-price-verification function and, where
required, the pricing/valuation committee. This skill hands those a cited pack; it never performs
them and never recommends a specific approve/override outcome.

## Upstream (may call this skill)

An end-of-day valuation-control process, an IPV queue, or `valuation-reviewer` may request a
price-level exception screen. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **pricing-exception checks only**; it must not reach a
  valuation determination, sign off IPV, or take/recommend a mark action — those belong to the
  human reviewer and the downstream skills.
- Downstream skills reuse the `review_id` evidence rather than recomputing the checks.
