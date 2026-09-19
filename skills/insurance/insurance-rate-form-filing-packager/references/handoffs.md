# Adjacent-Skill Handoffs — insurance-rate-form-filing-packager

Produces a cited filing-gap packet (`packet_id`) and stops. It does not submit, approve, or set
rates.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `pc-rate-adequacy-analyzer` with a qualified pricing actuary | Rate adequacy / actuarial support needs to be produced or refreshed | filing id + indicated-change gap |
| `insurance-data-reconciler` | Exhibit data provenance/consistency is questioned | exhibit refs |
| `policy-wording-comparator` | Form-language comparison across versions | form refs |

## Upstream (may call this skill)
Product-filing and compliance workflows may request a filing-completeness packet. This skill is
interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **checks completeness and evidences gaps**; it never submits, approves, or
  sets rates — those belong to the human, the filing system, and the regulator.
- Downstream reuses the `packet_id` evidence rather than recomputing.
