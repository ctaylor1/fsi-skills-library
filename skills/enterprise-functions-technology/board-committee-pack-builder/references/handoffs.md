# Adjacent-Skill Handoffs — board-committee-pack-builder

This skill **assembles** a pack from content other skills and people produce. It does not
generate the underlying analysis, and it does not deliver the pack or take the decisions.

## Upstream (feeds content into the pack)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `management-reporting-packager` | KPI/metrics, financial and control results, source lineage | cited metrics + source refs |
| `enterprise-risk-assessment-builder` | Risks, residual ratings, treatment actions, owners | cited risk items |
| `key-risk-indicator-monitor` | KRI values, threshold breaches, escalation commentary | cited indicators |
| `regulatory-change-impact-analyzer` | Regulatory/supervisory items with jurisdiction + effective dates | cited regulatory update items |
| `investment-committee-memo-builder` | Investment-committee memoranda when the pack is for an IC | cited memo + decision questions |
| `policy-document-assistant` | Policies/procedures tabled for approval | cited policy items |
| `enterprise-meeting-preparer` | Meeting brief, attendees, prior actions, logistics | non-substantive cover/agenda inputs |

The pack builder consumes these as **cited content items**; it re-cites, does not re-derive.

## Downstream (consumes the pack / follows the meeting)

| Downstream | When | Handoff artifact |
| ---------- | ---- | ---------------- |
| `meeting-action-tracker` | After the meeting, to extract decisions, owners, due dates, and open questions | the approved pack + minutes |

## Human / operations handoffs (no catalog skill)

- **Committee approval.** Decisions requiring approval are recorded as `proposed`; the
  committee members (humans) approve them in the meeting. The skill never approves.
- **Delivery / distribution.** The corporate secretariat delivers the approved pack via the
  board portal or approved channel. The skill never sends, submits, or distributes.
- **Legal / company-secretary review.** Governance, quorum, and disclosure questions go to
  the company secretary or legal counsel, not to this skill.

## Duplicate-execution prevention

- This skill **does not** compute metrics, rate risks, draft policies, or reach investment
  conclusions — those belong to the upstream skills, each cited.
- It **does not** track post-meeting actions — that is `meeting-action-tracker`.
- Approval and delivery are **human** steps; the pack records their requirement and status
  but never performs them.
