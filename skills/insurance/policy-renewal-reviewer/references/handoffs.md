# Adjacent-Skill Handoffs — policy-renewal-reviewer

This skill produces a cited **renewal comparison pack** (`review_id`) and stops. It does not
decide the renewal, price it, bind it, issue a notice, or make a coverage/claim determination.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `underwriting-workbench-assistant` | A renewal decision, re-rate, or bind is needed — compile the underwriter-ready profile and draft rationale for a **human** underwriter | `review_id` + fired findings |
| `policy-wording-comparator` | A `form_endorsement_change` finding fired and the wording impact needs clause-level comparison | changed `form_id`/editions |
| `coverage-gap-analyzer` | A `coverage_removed` / `limit_reduced` finding raises a coverage-adequacy question against the insured's needs | affected coverages + limits |
| `claims-file-reviewer` | A `large_open_claim` in the loss history needs deep file review (reserve, chronology, coverage evidence) | `claim_id` + loss window |
| `catastrophe-exposure-monitor` | Exposure change or accumulation needs modeled-loss / cat-accumulation monitoring | policy + exposure/location data |
| `premium-quote-comparator` | The user actually wants to compare **competing market quotes**, not expiring-vs-proposed on one policy | the quotes to normalize |
| `policy-document-explainer` | The user wants a plain explanation of a single policy document, not a renewal comparison | the document |

## Human / licensed-professional handoff (no skill substitutes)

- The **renewal decision** (renew / non-renew / decline), any **premium or rate**, **binding**, and
  **issuing a non-renewal or cancellation notice** are licensed-underwriter / carrier actions. This
  skill hands the human the comparison and the questions; it never makes or communicates the decision.
- **Personalized insurance advice** ("which option should the insured buy?") belongs to a licensed
  agent/broker, not this skill.

## Upstream (may call this skill)

Account-management and underwriting desks may request a renewal comparison at the start of the renewal
cycle. A scheduled monitor is **not** used here (this skill is interactive,
`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **findings and questions only**; it must not reach a disposition
  beyond the triage band, price, bind, or issue a notice — those belong to the human and the downstream
  skills.
- Downstream skills reuse the `review_id` comparison rather than recomputing the term diff.
