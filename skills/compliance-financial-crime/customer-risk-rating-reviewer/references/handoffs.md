# Handoffs

Upstream: the authorized case owner supplies scoped original records, the applicable policy profile, owner/audience/classification, assessment date and identified evidence gaps. No connector integration is bundled.

| Receiver | Trigger and boundary |
|---|---|
| `customer-due-diligence-reviewer` | Missing customer/identity/ownership data goes to the CDD analyst. |
| `sanctions-match-investigator` | A separate potential sanctions concern; score alone cannot establish prohibition. |
| `adverse-media-investigator` | Unresolved media identity/materiality evidence. |
| `enhanced-due-diligence-assessor` | EDD evidence assembly when required by the applicable human-reviewed policy. |
| `transaction-monitoring-scenario-evaluator` | A separately scoped transaction-monitoring trigger. |

Pass the native result, the separately retained original input reference and a separate evidence/workflow envelope. The receiver must validate producer output against that original and validate its own native input. Carry unresolved issues, source status and applicability limits unchanged; a successful producer check does not satisfy receiver preconditions or authorize a customer decision.

Use [evidence contract](evidence-contract.md) and [source governance](source-governance.md). The agent recommends these routes; it does not automatically send, submit, update or execute them. A human determines legal or policy decisions and any subsequent authorized action.
