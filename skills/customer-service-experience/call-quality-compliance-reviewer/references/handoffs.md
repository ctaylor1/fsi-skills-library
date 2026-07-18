# Adjacent-Skill Handoffs — call-quality-compliance-reviewer

This skill produces a cited **quality/compliance scorecard** (`review_id`) and stops. It
does not disposition the case, deliver coaching, remediate, file, or act.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `complaint-resolution-assistant` | The interaction contains a substantive complaint to classify, root-cause, remediate, and respond to | `review_id` + complaint finding + turns |
| `service-recovery-assistant` | A service failure needs impact assessment and remediation/goodwill designed for approval | `review_id` + finding evidence |
| `vulnerable-customer-support-assistant` | A vulnerability cue was missed and the customer needs accommodation/specialist referral | `review_id` + vulnerability finding |
| `operational-risk-event-analyzer` | A compliance-critical finding rises to a loss/near-miss operational-risk event to classify | `review_id` + critical findings |
| `communications-compliance-reviewer` | The item is actually a written/marketing or supervised communication, not a contact-center interaction | interaction ref + content |
| `customer-interaction-summarizer` | The user really wants a plain summary (sentiment, actions), not a rubric review | interaction ref |

## Upstream (may call this skill)

`omnichannel-case-orchestrator` and QA workflows may request a scorecard; a
`customer-interaction-summarizer` output can seed the transcript context. A scheduled
monitor is **not** used here (this skill is interactive, `aws-fsi-scheduled-agent: no`).

## Human / operations handoffs (no catalog skill)

- **Coaching delivery** to the agent or team lead is a **human** step — this skill suggests a
  coaching disposition and evidence, but a QA lead delivers it.
- **Disciplinary / HR action** is a **human HR** decision, never produced here.
- **Regulatory-reporting decisions** (whether a matter is reportable) belong to the
  **compliance officer / licensed specialist**, not this skill.

## Duplicate-execution prevention

- This skill computes and evidences **findings only**; it must not reach a disposition,
  deliver coaching, contact the customer, remediate, or file — those belong to the human
  reviewer and the downstream skills.
- Downstream skills reuse the `review_id` evidence rather than recomputing the checks.
