<!--
Credit Application Package — output template (credit-package-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest; every included/stale/unresolved item MUST carry its citation.
This is a DRAFT for human review — never a certification, decision, or delivery.
-->

# Credit Application Package (DRAFT) — {{package_id}}

> Draft credit package for human review only. This package is not a completeness
> certification, not a credit decision or adverse-action notice, and has not been submitted
> or delivered.

## Package Summary
- Package ID: {{package_id}}
- Product: {{product}} | Jurisdiction: {{jurisdiction}}
- As-of date: {{as_of_date}}
- Config / template version: {{config_version}} / {{template_version}}
- Assembly status: **draft-assembled**
- Human approval required before delivery: **yes**
- Counts: included {{n_included}} · stale {{n_stale}} · unresolved {{n_unresolved}} · missing {{n_missing}} · open items {{n_open_items}}

## Borrower Profile
- Legal name: {{borrower_legal_name}}
- Borrower ID (masked): {{borrower_id_masked}}
- Entity type: {{borrower_entity_type}}

## Application
- {{application_status}} — {{application_title}} ({{application_doc_id}}) — cite: {{application_citation}}
- Key values: {{application_values}}

## Financial Information
For each financial document (statements, tax returns, spreads):
- {{status}} — {{title}} ({{doc_id}}) — cite: {{citation}} {{stale_or_unresolved_reason}}

## Collateral
- {{collateral_status}} — {{collateral_title_or_open_item}} — cite: {{collateral_citation}}

## KYC / Onboarding
- {{kyc_status}} — {{kyc_title}} ({{kyc_doc_id}}) — cite: {{kyc_citation}} {{unresolved_reason}}

## Approvals
Recorded:
- {{approval_type}} — {{approver_role}} — {{approval_date}} — cite: {{approval_citation}}

Outstanding (required, not yet recorded):
- {{outstanding_approval_type}} — status: outstanding

## Open Items
Every item requiring human action before this package can be certified/delivered:
- [{{open_item_type}}] {{open_item}} — action: {{required_action}} {{open_item_citation}}

## Source Index
Deduplicated citations backing every asserted item in this package:
- {{citation}}

---
Handoff: route to loan-package-completeness-checker for formal completeness certification.
This skill assembles only — completeness certification and the credit decision are separate,
human-owned control steps.
