# Adjacent-Skill Handoffs — insurance-rating-quote-worksheet

Produces an indicated-premium worksheet (`worksheet_id`) and stops. It does not bind coverage,
issue a quote, or make an offer.

## Downstream (route the human/analyst to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `insurance-regulatory-filing-packager` | The rating supports a rate/rule filing | worksheet id + factors |
| `actuarial-model-run-assistant` | Rate adequacy / loss development is needed | risk/segment refs |

## Upstream (may call this skill)
Underwriting workflows may request a rating worksheet before quoting. This skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **computes the indicated premium and shows the math**; it never binds, quotes,
  or offers — those belong to underwriting.
- Downstream reuses the `worksheet_id` worksheet rather than recomputing.
