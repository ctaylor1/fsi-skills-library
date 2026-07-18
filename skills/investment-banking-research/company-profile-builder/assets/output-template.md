<!--
Company Profile / Strip Page — output template (profile-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest; every asserted (included/stale/unresolved) fact MUST carry its
citation. Unsourced facts and MNPI (in an external profile) are NEVER asserted here — they
appear only under Open Items. This is a DRAFT for human review — never advice, a rating, a
recommendation, or a delivery.
-->

# Company Profile (DRAFT) — {{company_legal_name}} ({{ticker}})

> Draft company profile for human review only. This profile is not investment advice or a
> recommendation, every stated fact is source-cited, and it has not been distributed or
> delivered. Confidential — MNPI / client-confidential.

## Profile Summary
- Profile ID: {{profile_id}}
- Company: {{company_legal_name}} ({{ticker}}) | Entity type: {{entity_type}}
- As-of date: {{as_of_date}} | Intended distribution: {{intended_distribution}}
- Config / template version: {{config_version}} / {{template_version}}
- Assembly status: **draft-assembled**
- Human approval required before delivery: **yes**
- Counts: included {{n_included}} · stale {{n_stale}} · unresolved {{n_unresolved}} · excluded (MNPI) {{n_mnpi}} · unsupported {{n_unsupported}} · open items {{n_open_items}}

## Business Overview
For each asserted fact:
- {{status}} — {{label}}: {{value}} — cite: {{citation}}

## Key Financials
For each asserted KPI / financial metric:
- {{status}} — {{label}}: {{value}} — cite: {{citation}}

## Ownership
For each asserted holder / share-structure fact:
- {{status}} — {{label}}: {{value}} — cite: {{citation}} {{unresolved_reason}}

## Management
For each asserted executive / board fact:
- {{status}} — {{label}}: {{value}} — cite: {{citation}}

## Trading Data
For each asserted market-data fact (as-of dated):
- {{status}} — {{label}}: {{value}} — cite: {{citation}} {{stale_reason}}

## Transactions
For each asserted precedent M&A / financing fact:
- {{status}} — {{label}}: {{value}} — cite: {{citation}}

## Approvals
Recorded:
- {{approval_type}} — {{approver_role}} — {{approval_date}} — cite: {{approval_citation}}

Outstanding (required, not yet recorded):
- {{outstanding_approval_type}} — status: outstanding

## Open Items
Every gap requiring human action before this profile can be approved/distributed:
- [{{open_item_type}}] {{open_item}} — action: {{required_action}} {{open_item_citation}}

## Sources
Deduplicated citations backing every asserted fact in this profile:
- {{citation}}

---
Handoff: route the assembled `profile_id` + manifest to `investment-banking-pitch-builder`
(deck) or `coverage-meeting-preparer` (briefing). This skill assembles only — investment
advice/ratings, MNPI clearance, approval, and external distribution are separate,
human/compliance-owned steps.
