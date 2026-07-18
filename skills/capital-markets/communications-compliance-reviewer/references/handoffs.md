# Adjacent-Skill Handoffs — communications-compliance-reviewer

This skill produces a cited **communications-review pack** (`review_id`) with findings and a
recommended disposition, then stops. It does not approve, file, close the review, or
investigate to disposition. Registered-principal adjudication is mandatory.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `surveillance-alert-triager` | A communication contains language indicating possible MNPI misuse or market abuse | `review_id` + flagged excerpt |
| `market-surveillance-alert-investigator` | An escalated electronic-communications surveillance matter needs full investigation | `review_id` + evidence |
| `complaint-resolution-assistant` | The communication contains or references a customer complaint | `review_id` + excerpt |
| `conflicts-of-interest-reviewer` | The communication surfaces a potential conflict of interest to assess | `review_id` + excerpt |
| `regulatory-exam-response-packager` | The review evidence must be assembled for an exam or regulatory request | `review_id` + findings |

## Upstream (may call this skill)

Skills that draft or assemble communications route their draft here for a compliance review
**before** external delivery or principal approval — for example `advisor-follow-up-assistant`
(client communications and disclosures), `fund-commentary-drafter` (fund commentary), and
`investment-banking-pitch-builder` (pitch material). A scheduled monitor is **not** used here
(this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Not this skill

- A **voice/phone interaction** review belongs to `call-quality-compliance-reviewer`, not here;
  this skill reviews written/electronic and published material.
- The **regulated decision** — approving the communication, filing it, or closing the review —
  is performed by a **registered principal** in the supervision system of record, never by this
  skill or any handoff skill on its behalf.

## Duplicate-execution prevention

- This skill computes and evidences **findings only**; it must not approve, file, close, or
  reach a disposition — those belong to the registered principal.
- Downstream skills reuse the `review_id` evidence rather than recomputing the review.
