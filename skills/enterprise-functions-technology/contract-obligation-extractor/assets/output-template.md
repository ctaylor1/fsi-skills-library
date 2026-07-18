<!--
Contract Obligation Register — output template (obligation-register-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest; every extracted/ambiguous/conflict item MUST carry its clause
citation. This is a DRAFT extraction aid for human review — never legal advice, a
completeness certification, or a delivered/executed document.
-->

# Contract Obligation Register (DRAFT) — {{register_id}}

> Draft obligation register for human review only. This register is an extraction aid, not
> legal advice or a completeness certification, and it has not been delivered, executed, or
> acted on. Every obligation must be verified against the source contract.

## Register Summary
- Register ID: {{register_id}}
- Contract: {{contract_id}} — {{title}} | Counterparty: {{counterparty}}
- As-of date: {{as_of_date}}
- Config / template version: {{config_version}} / {{template_version}}
- Assembly status: **draft-extracted**
- Human approval required before delivery: **yes**
- Counts: extracted {{n_extracted}} · ambiguous {{n_ambiguous}} · conflict {{n_conflict}} · coverage gaps {{n_coverage_gap}} · unsourced {{n_unsourced}} · open items {{n_open_items}}

## Contract Profile
- Contract ID: {{contract_id}} | Type: {{contract_type}}
- Counterparty: {{counterparty}}
- Effective date: {{effective_date}} | Term end: {{term_end}}
- Governing law: {{governing_law}} — cite: {{contract_citation}}

## Obligations
For each obligation (who must do what, by when):
- [{{status}}] {{summary}} — responsible: {{responsible_party}} — clause {{clause_ref}} — cite: {{citation}} {{reason_if_ambiguous_or_conflict}}

## Key Dates
Effective dates, expiries, milestones, and deadlines:
- [{{status}}] {{summary}} — due/trigger: {{due}} — clause {{clause_ref}} — cite: {{citation}}

## Service Levels
- [{{status}}] {{summary}} — responsible: {{responsible_party}} — clause {{clause_ref}} — cite: {{citation}}

## Rights & Restrictions
Rights granted and restrictions imposed (audit, non-solicit, exclusivity, IP, etc.):
- [{{status}}] {{summary}} — responsible: {{responsible_party}} — clause {{clause_ref}} — cite: {{citation}}

## Renewal & Termination
Auto-renewal, non-renewal notice, termination rights and notice periods:
- [{{status}}] {{summary}} — notice: {{notice_days}} days — clause {{clause_ref}} — cite: {{citation}} {{reason_if_conflict}}

## Data Terms
Data protection, processing role, breach notification, sub-processor, and residency terms:
- [{{status}}] {{summary}} — responsible: {{responsible_party}} — clause {{clause_ref}} — cite: {{citation}}

## Dependencies
Cross-references, incorporated documents, third-party and inter-contract dependencies:
- [{{status}}] {{summary}} — clause {{clause_ref}} — cite: {{citation}}
- (coverage-gap) {{category}} — no clause mapped — action: confirm whether the contract addresses this; do not assume silence

## Reviews
Recorded human reviews:
- {{review_type}} — {{reviewer_role}} — {{review_date}} — cite: {{review_citation}}

Outstanding (required, not yet recorded):
- {{outstanding_review_type}} — status: outstanding

## Open Items
Every item requiring human action before this register can be relied on or delivered:
- [{{open_item_type}}] {{open_item}} — action: {{required_action}} {{open_item_citation}}

## Source Index
Deduplicated clause citations backing every asserted item in this register:
- {{citation}}

---
Handoffs: financial covenants requiring ongoing monitoring → covenant-compliance-monitor;
counterparty/vendor risk from data terms and dependencies → third-party-risk-assessor;
turning obligations and key dates into tracked action items → meeting-action-tracker. Legal
interpretation, enforceability, breach, or negotiation questions go to licensed legal
counsel. This skill extracts and cites only — it never advises, certifies completeness, or
delivers.
