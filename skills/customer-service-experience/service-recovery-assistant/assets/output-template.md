# Service-Recovery Package — DRAFT FOR APPROVAL

> Draft for human review only; no communication has been sent and no goodwill or redress has
> been paid. Every figure below is a computed value bounded by the approved matrix; every
> claim is cited. Fill the approval block before any external delivery.

**Case ID:** `{{case_id}}`  |  **Customer:** `{{customer_ref (masked)}}`  |
**Failure type:** `{{failure_type}}`  |  **Disposition:** `draft-for-approval`

---

## 1. Case summary
`{{one-line summary of the service failure and who it affected}}`

## 2. Failure assessment
- **Severity band:** `{{High|Medium|Low}}` (score `{{n}}`) — `{{severity_reason}}`
- **Citations:** `{{crm/call/policy refs}}`

## 3. Customer impact
- **Impact band:** `{{High|Medium|Low}}` (score `{{n}}`) — `{{impact_reason}}`
- **Financial detriment:** `{{$amount}}` (documented: `{{yes|no}}`)
- **Vulnerability flag:** `{{yes|no}}` — if yes, route to vulnerable-customer-support-assistant

## 4. Precedent & policy
- **Applicable policy / product terms:** `{{policy_refs}}`
- **Comparable precedent:** `{{count and range of prior remediations for this failure type}}`
- **Fair-value note:** Remediation is a proposal bounded by the approved goodwill matrix; it
  is not a determination of legal liability.
- **Citations:** `{{refs}}`

## 5. Proposed remediation
| Component | Amount |
| --------- | ------ |
| Direct redress (documented detriment) | `{{$redress}}` |
| Goodwill gesture (matrix `{{severity}}`×`{{impact}}`) | `{{$goodwill}}` |
| **Total** | **`{{$total}}`** |

- **Matrix version:** `{{config_version}}`  |  **Within cap (≤ $200):** `{{yes}}`
- **Reason codes:** `{{severity:.. impact:.. matrix:..}}`

## 6. Draft customer communication (approved language only)
- **Apology:** `{{approved apology — acknowledges the failure, no liability admission}}`
- **Explanation:** `{{what happened, grounded in cited policy/terms}}`
- **Remediation offer:** `{{"Subject to approval, we would like to ... This comes to $total in total."}}`
- **Next steps:** `{{confirmation on approval; invite correction}}`
- **Citations:** `{{refs}}`

## 7. Required approvals
- **Authority tier:** `{{agent|team_lead|manager}}`
- **Approver role:** `{{role}}`
- **Status:** `pending`  |  **Approver:** `{{unfilled}}`  |  **Decision:** `{{unfilled}}`

## 8. Sources & citations
`{{full citation list}}`

---

### Handling
Draft only. On approval at the tier above, delivery and any goodwill/redress payment are
performed by authorized operations (`omnichannel-case-orchestrator` / approval broker) — not
by this skill. Formal complaints go to `complaint-resolution-assistant`.
