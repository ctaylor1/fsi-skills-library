# Adjacent-Skill Handoffs — communications-compliance-reviewer

This skill produces a cited **communications-review pack** (`review_id`) with findings and a
recommended disposition, then stops. It does not approve, file, close the review, or
investigate to disposition. Registered-principal adjudication is mandatory.

## Promotion ownership

`financial-promotion-reviewer` owns external cross-sector financial-promotion
assessment. This Capital Markets package supplies a broker-dealer supervision and
records screen only when that institutional/jurisdiction profile is applicable.
Authors in Wealth, Asset Management, Investment Banking, Banking and Insurance
route external promotions to that primary owner and add this specialist if needed.
Keep each native schema, evidence version and professional conclusion separate;
no implicit common handoff or regulatory approval is established by this link.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `surveillance-alert-triager` | A communication contains language indicating possible MNPI misuse or market abuse | `review_id` + flagged excerpt |
| `market-surveillance-alert-investigator` | An escalated electronic-communications surveillance matter needs full investigation | `review_id` + evidence |
| `complaint-resolution-assistant` | The communication contains or references a customer complaint | `review_id` + excerpt |
| `conflicts-of-interest-reviewer` | The communication surfaces a potential conflict of interest to assess | `review_id` + excerpt |
| `regulatory-exam-response-packager` | The review evidence must be assembled for an exam or regulatory request | `review_id` + findings |

## Upstream (may call this skill)

Skills that draft or assemble communications route external promotion drafts to `financial-promotion-reviewer`, composing this specialist for broker-dealer supervision review
**before** external delivery or principal approval — for example `advisor-follow-up-assistant`
(client communications and disclosures), `investment-commentary-builder` (fund commentary), and
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
