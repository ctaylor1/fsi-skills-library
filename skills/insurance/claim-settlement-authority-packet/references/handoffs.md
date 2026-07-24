# Adjacent-Skill Handoffs — claim-settlement-authority-packet

Produces a cited settlement-authority *request* packet (`packet_id`) and stops. It does not
approve a settlement, grant authority, or authorize payment.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `liability-evidence-matrix-builder` | The liability evidence base needs mapping | claim id + facts |
| `claim-damage-evaluation-comparator` | Damage documents/line items need comparison | claim id + document refs |

## Upstream (may call this skill)
Claims-handling workflows may request an authority packet before routing for approval. This skill
is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **packages the request and looks up the required tier**; it never approves,
  grants authority, or authorizes payment — those belong to the authorized approver.
- Downstream/approvers reuse the `packet_id` request rather than rebuilding.
