# Handoffs

| Adjacent skill / human | Trigger | Artifact |
| --- | --- | --- |
| `account-anomaly-screener` | Generic bank activity anomaly analysis is needed | Bounded transaction evidence and source IDs |
| `vulnerable-customer-support-assistant` | Customer support accommodations are needed | Minimized customer-provided support context |
| `investment-recommendation-evidence-reviewer` | Investment recommendation concerns dominate | Profile, recommendation and cited concern evidence |
| `suspicious-activity-report-drafter` | Authorized reviewer requests a SAR draft | Restricted cited pack, explicit authorized scope |
| `complaint-resolution-assistant` | Service/handling grievance | Complaint record, minimum necessary context |
| `client-review-preparer` | Routine review without safeguarding concerns | Appropriate non-restricted summary |
| Supervisor / compliance / safeguarding specialist | Any concern, unknown applicability or evidence needing adjudication | artifact_id, full input hash, sources, gaps and review priority |

Humans own determinations, holds, contacts, reports and closure. No handoff auto-executes.
The full digest prevents same-household/day collisions. Source evidence may be reused; the
recipient checks scope, freshness, permissions and unresolved findings before relying on it.
