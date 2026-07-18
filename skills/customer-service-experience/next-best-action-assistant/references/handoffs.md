# Adjacent-Skill Handoffs — next-best-action-assistant

Recommending next-best-actions is a **drafting** activity. Binding decisions, complaint
handling, and licensed advice are **separate control activities** with different entitlements.
This skill emits a draft package; it must not perform another skill's decision.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `customer-interaction-summarizer` | Interaction summary, sentiment, commitments, and open actions used as context signals |
| `omnichannel-case-orchestrator` | Unified customer history / case context across channels |
| `knowledge-answer-composer` | Source-linked answers the agent may pair with an education action |

## Downstream / boundary routing (this skill refers to)

| Route to | When | Handoff artifact |
| -------- | ---- | ---------------- |
| `suitability-reg-bi-reviewer` | Any investment allocation / suitability question (prohibited as an NBA recommendation) | customer_ref + the excluded action + context |
| `investment-policy-statement-builder` / `portfolio-proposal-comparator` | Downstream of a licensed adviser once advice is appropriate | licensed adviser's engagement |
| `senior-investor-protection-screener` | Older-investor protection concerns surface | customer_ref + trigger context |
| `loan-affordability-precheck` / `credit-application-packager` | Customer is shopping for credit; NBA drafts a **referral**, not a decision | customer_ref + referral note |
| `complaint-resolution-assistant` | The interaction is (or becomes) a complaint | customer_ref + complaint context |
| `service-recovery-assistant` | A service failure needs remediation/fair-value assessment | customer_ref + failure context |
| `vulnerable-customer-support-assistant` | Vulnerability flag present; retention/cross-sell suppressed | customer_ref + suppression note |
| `call-quality-compliance-reviewer` | Post-hoc QA of how a recommendation was delivered | interaction reference |

Where no catalog skill fits (e.g., the actual mortgage credit decision, a claims coverage
determination), the handoff is to a **licensed human specialist / operations team**, not an
automated skill. NBA never makes or communicates that decision.

## Duplicate-execution prevention

- This skill **does not** decide credit, claims, or investment suitability, resolve
  complaints, or deliver communications — those belong to the skills/specialists above.
- Recommendations are **proposals**; a human approves and an entitled downstream step delivers.
- A prohibited action is routed once (recorded in `specialist_referrals`), not re-attempted as
  a recommendation.
