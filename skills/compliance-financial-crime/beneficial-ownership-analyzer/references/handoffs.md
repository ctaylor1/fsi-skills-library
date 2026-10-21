# Handoffs

Upstream: the authorized case owner supplies scoped original records, the applicable policy profile, owner/audience/classification, assessment date and identified evidence gaps. No connector integration is bundled.

| Receiver | Trigger and boundary |
|---|---|
| `customer-due-diligence-reviewer` | Return candidate/coverage evidence and remediation gaps to the CDD analyst. |
| `enhanced-due-diligence-assessor` | Provide bounded ownership analysis as one EDD evidence input. |
| `sanctions-match-investigator` | Use only for a separate potential sanctions concern; ownership arithmetic here is not a sanctions ownership rule. |

Pass the native result, the separately retained original input reference and a separate evidence/workflow envelope. The receiver must validate producer output against that original and validate its own native input. Carry unresolved issues, source status and applicability limits unchanged; a successful producer check does not satisfy receiver preconditions or authorize a customer decision.

Use [evidence contract](evidence-contract.md) and [source governance](source-governance.md). The agent recommends these routes; it does not automatically send, submit, update or execute them. A human determines legal or policy decisions and any subsequent authorized action.
