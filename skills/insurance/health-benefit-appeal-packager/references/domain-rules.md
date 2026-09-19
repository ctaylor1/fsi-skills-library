# Domain rules — Health Benefit Appeal Packaging

- Scope is health benefit administrative appeals. Other insurance segments are rejected; carrier denial rationale drafting belongs to a separate role/workflow.
- Document type only satisfies administrative inventory. It cannot support a statement that the service met plan criteria. Argument points quote supplied reason-specific passages and identify the member’s proposed relevance for human assessment.
- Evidence doc_ref must resolve to a supplied document. Policy references attach only when explicitly linked by that reason’s evidence; no blanket attachment of every policy provision.
- Unknown reason codes create a plan-specific review gap. Missing passages create a reason-specific evidence gap even if every requested document type is present.
- Deadline = supplied start event date + supplied calendar-day appeal window, with status relative to as_of. Missing controlling start-event evidence is an unverified estimate and blocks ready_to_draft. This does not establish the legal appeal deadline, extensions, emergency/expedited rights or external review path.
- Readiness is gaps_present whenever any evidence/deadline gap remains. A grounded draft remains subject to human review and has never been filed.
- Preserve quoted denial/clinical/member statements, but do not turn them into assistant coverage or medical conclusions.

## Scope limit
Health administrative evidence packaging only; no medical necessity analysis, medical opinion, legal advice, external-review eligibility determination, denial generation or appeal submission.
