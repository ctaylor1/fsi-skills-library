# Handoffs

Upstream: the authorized case owner supplies scoped original records, the applicable policy profile, owner/audience/classification, assessment date and identified evidence gaps. No connector integration is bundled.

| Receiver | Trigger and boundary |
|---|---|
| `sanctions-match-investigator` | Potential sanctions proximity, with unresolved identity explicitly preserved. |
| `customer-due-diligence-reviewer` | PEP identity/risk assessment by the CDD/EDD analyst. |
| `enhanced-due-diligence-assessor` | Supported media indicator and unresolved evidence for EDD review; never investment-banking VDR packaging. |
| `customer-risk-rating-reviewer` | Supply scoped media evidence for an applicable customer-risk methodology; no rating update is performed here. |

Pass the native result, the separately retained original input reference and a separate evidence/workflow envelope. The receiver must validate producer output against that original and validate its own native input. Carry unresolved issues, source status and applicability limits unchanged; a successful producer check does not satisfy receiver preconditions or authorize a customer decision.

Use [evidence contract](evidence-contract.md) and [source governance](source-governance.md). The agent recommends these routes; it does not automatically send, submit, update or execute them. A human determines legal or policy decisions and any subsequent authorized action.
