# Adjacent-Skill Handoffs — comps-analysis-builder

Building a comparable-company analysis (this skill) is a **separate activity** from intrinsic
valuation modeling, from the valuation conclusion / independent review, and from assembling a
client deliverable. This skill emits a durable `analysis_id` and a cited comps manifest; it does
not perform the modeler's, reviewer's, or pitch-builder's work.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `dcf-modeler` | An intrinsic cross-check against the market multiples is needed, or comps-implied exit multiples feed a DCF | `analysis_id` + summary statistics + implied range |
| `valuation-reviewer` | Independent review of the comps methodology, peer selection, inputs, and adjustments is needed | `analysis_id` + manifest + source index |
| `investment-banking-pitch-builder` | The finished comps page is placed into a banker-reviewed client pitch book | `analysis_id` + rendered comps section + citations |
| `scenario-sensitivity-generator` | Multiple ranges are stress-tested across scenarios | `analysis_id` + summary statistics |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `earnings-results-analyzer` | Latest reported/adjusted operating metrics per peer for the LTM basis |
| `three-statement-model-builder` | Projected (FY1/forward) revenue and EBITDA for forward multiples |
| `company-profile-builder` | Peer business overview and trading data used in the peer rationale |
| `market-landscape-researcher` | Candidate peer universe and sub-industry mapping |
| `financial-spreading-assistant` | Normalized/spread financials when reported figures need reclassification |

## Non-catalog handoffs (human / licensed)

- **Valuation conclusion / fairness opinion** → a licensed valuation professional or the deal's
  valuation committee. No catalog skill issues a binding valuation opinion or a recommendation.
- **Peer-set sign-off and external delivery** → the coverage banker / supervisory analyst
  approves the peer set and delivers to the client via the approval broker; this skill never
  selects peers to steer a result, and never sends or submits.
- **Wall-crossing / information-barrier decisions** → compliance / the control room. This skill
  uses non-public data-room figures only for a user already wall-crossed and permissioned.

## Duplicate-execution prevention

- This skill **does not** build the intrinsic DCF, opine on value, review its own methodology,
  or assemble the pitch — those belong to the named skills or to a human.
- Downstream skills consume this skill's `analysis_id` / manifest rather than rebuilding the
  comps.
- A peer excluded by the criteria is left as an `excluded` open item for human confirmation,
  never silently dropped or re-added.
