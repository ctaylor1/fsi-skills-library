<!--
Procurement Sourcing Pack — output template (sourcing-pack-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest; every asserted item (requirement, supplier, bidder score, RFP
section, risk input) MUST carry its citation. This is a DRAFT for human review — it ranks and
recommends only; it never awards, selects, issues, sends, or negotiates.
-->

# Procurement Sourcing Pack (DRAFT) — {{sourcing_id}}

> Draft sourcing pack for human review only. This pack ranks bidders and recommends a preferred
> option for approval; it makes no sourcing decision, creates no purchasing commitment, and has
> not been issued, sent, or negotiated. Any award, delivery, or negotiation is a separate,
> human-approved step.

## Pack Summary
- Sourcing ID: {{sourcing_id}}
- Category: {{category}} | Jurisdiction: {{jurisdiction}}
- As-of date: {{as_of_date}}
- Config / template version: {{config_version}} / {{template_version}}
- Pack status: **draft-assembled**
- Award decision: **pending-human-approval**
- Human approval required before delivery: **yes**
- Counts: requirements {{n_requirements}} · suppliers {{n_suppliers}} · criteria {{n_criteria}} · bidders scored {{n_scored}} / knockout {{n_knockout}} / needs-data {{n_needs_data}} · approvals recorded {{n_appr_recorded}} / outstanding {{n_appr_outstanding}} · open items {{n_open_items}}

## Requirements
For each requirement (business / functional / technical):
- [{{priority}}] {{status}} — {{req_text}} ({{req_id}}) — owner: {{owner}} — cite: {{citation}}

## Market Scan
Candidate suppliers identified (context, not a recommendation):
- {{status}} — {{supplier_name}} ({{supplier_id}}, {{segment}}) — cite: {{citation}}

## Evaluation Criteria
Weighted scoring model (weights sum to {{weight_total}}; expected 100):
- {{criterion_name}} ({{criterion_id}}) — weight {{weight}} — mandatory: {{mandatory}} — cite: {{citation}}

## RFP Content
Drafted RFP/RFI sections (draft only — not issued):
- {{status}} — {{section_title}} ({{section_id}}) — cite: {{citation}}

## Bidder Comparison
Deterministic weighted scorecard (score 0–10 per criterion; weighted_score on a 0–10 scale):
- {{status}} — {{bidder_name}} ({{bidder_id}}) — weighted_score: {{weighted_score}} — scores: {{scores}} — cite: {{citation}} {{knockout_or_needs_data_reason}}

## Risk Inputs
Vendor-risk items routed to the specialist skills (not adjudicated here):
- [{{risk_type}}] {{description}} — route: {{route}} — status: routed — cite: {{citation}}

## Decision Record
- Draft recommendation: {{recommended_bidder_name}} ({{recommended_bidder_id}}) — weighted_score {{recommended_weighted_score}} — status: **recommended-pending-approval**
- Rationale: {{rationale}}
- Award decision: **pending-human-approval**

Approvals — recorded:
- {{approval_type}} — {{approver_role}} — {{approval_date}} — cite: {{approval_citation}}

Approvals — outstanding (required, not yet recorded):
- {{outstanding_approval_type}} — status: outstanding

Open items (human action required before this pack can support an award decision):
- [{{open_item_type}}] {{open_item}} — action: {{required_action}} {{open_item_citation}}

## Source Index
Deduplicated citations backing every asserted item in this pack:
- {{citation}}

---
Handoff: route risk items to third-party-risk-assessor / third-party-cyber-risk-reviewer /
third-party-ai-due-diligence-assistant; route the recommendation to the sourcing lead or
procurement committee (or board-committee-pack-builder) for the award decision. This skill
assembles and recommends only — the award, RFP issuance, vendor-risk determinations, and
contract execution are separate, human-owned steps.
