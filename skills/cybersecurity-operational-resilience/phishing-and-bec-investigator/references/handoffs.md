# Adjacent-Skill Handoffs — phishing-and-bec-investigator

Triage, investigation, containment, and recovery are **separate control activities** with
different entitlements, evidence depth, and case states. This skill is the **investigation**
stage: it consumes a triaged report and emits a durable `case_id` + evidence bundle +
disposition recommendation. It does not triage, execute containment, remediate access, or
recover funds.

## Upstream (feeds this skill)

| Upstream skill | Handoff artifact |
| -------------- | ---------------- |
| `security-alert-triage-assistant` | Enriched, prioritized email/security alert with mapped assets and identities, ready for investigation |

A read-only monitor may *populate* the reported-message queue, but must not investigate or act.

## Downstream / routing (this skill recommends and routes to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `payment-fraud-case-investigator` | BEC with a fraudulent payment / vendor bank-change request | `case_id` + amounts + beneficiary evidence |
| `cyber-incident-response-coordinator` | Confirmed-worthy phishing incident needing coordinated containment across the org | `case_id` + evidence bundle + recommended containment |
| `identity-access-reviewer` | Credential exposure / suspected account takeover of recipients or an internal sender | `case_id` + affected-identity evidence |
| `data-loss-prevention-incident-assistant` | The lure or a reply indicates data exfiltration / policy violation | `case_id` + exposure evidence |

If no catalog skill fits (e.g., contacting the beneficiary bank, notifying law enforcement,
or a regulatory filing), the step is routed to the **human incident commander / fraud
operations / legal** as a recommendation — never executed by this skill, and never invented
as a skill name.

## Duplicate-execution prevention

- This skill **does not** triage, execute containment, reset access, or recall payments —
  those belong to the skills above and to human approvers.
- A downstream skill consumes the investigation `case_id` / bundle rather than re-investigating.
- A `possible-duplicate` report is **linked** to its open parent case and resolved by a
  human, never auto-merged or auto-closed here.
