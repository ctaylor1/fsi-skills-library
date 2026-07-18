<!--
Fund Fact Sheet — output template (factsheet-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest; every asserted (included/stale/unresolved) figure MUST carry its
citation, and every numeric figure MUST tie to its source value in the reconciliation ledger.
Unsourced figures, unreconciled figures, and MNPI/embargoed facts (in an external sheet) are
NEVER asserted here — they appear only under Open Items. Regulatory disclosures are approved,
cited controlled content. This is a DRAFT for human review — never a return promise, a rating,
a recommendation, or a delivery.
-->

# Fund Fact Sheet (DRAFT) — {{fund_legal_name}} — {{share_class}}

> Draft fund fact sheet for human review only. Every figure is source-cited and reconciled to
> its system of record, past performance is not indicative of future results, and this fact
> sheet has not been reviewed, approved, or distributed. Confidential — MNPI / client-confidential.

## Fund Summary
- Fact sheet ID: {{factsheet_id}}
- Fund: {{fund_legal_name}} — {{share_class}} | ISIN {{isin}} | Ticker {{ticker}} | Currency {{currency}}
- Inception: {{inception_date}} | Benchmark: {{benchmark_name}}
- Investment objective: {{objective}}
- As-of (reporting) date: {{as_of_date}} | Intended distribution: {{intended_distribution}}
- Config / template version: {{config_version}} / {{template_version}}
- Assembly status: **draft-assembled**
- Human approval required before delivery: **yes**
- Counts: included {{n_included}} · stale {{n_stale}} · unresolved {{n_unresolved}} · excluded (MNPI) {{n_mnpi}} · unsupported {{n_unsupported}} · reconcile breaks {{n_reconcile_break}} · open items {{n_open_items}}

## Performance
Standardized, net-of-fees returns as of the reporting date. For each asserted figure:
- {{status}} — {{label}}: {{value}} ({{basis}}) — cite: {{citation}}

## Holdings
Top holdings and portfolio allocation. For each asserted figure:
- {{status}} — {{label}}: {{value}} — cite: {{citation}}

## Risk
Risk metrics and indicators (as-of dated). For each asserted figure:
- {{status}} — {{label}}: {{value}} — cite: {{citation}} {{stale_reason}}

## Fees
Ongoing charges and fees. For each asserted figure:
- {{status}} — {{label}}: {{value}} — cite: {{citation}} {{unresolved_reason}}

## ESG
Sustainability classification and metrics. For each asserted figure:
- {{status}} — {{label}}: {{value}} — cite: {{citation}}

## Source Reconciliation
Every numeric figure tied to its system-of-record value (source-to-output reconciliation):
- {{reconcile_status}} — {{label}} ({{fact_id}}): output {{value_numeric}} vs source {{source_value_numeric}} (delta {{delta}}, tolerance {{tolerance}}) — cite: {{citation}}

## Disclosures
Required regulatory disclosures (approved, cited controlled content):
- {{disclosure_id}}: {{disclosure_text}} — cite: {{disclosure_citation}}

## Approvals
Recorded:
- {{approval_type}} — {{approver_role}} — {{approval_date}} — cite: {{approval_citation}}

Outstanding (required, not yet recorded):
- {{outstanding_approval_type}} — status: outstanding

## Open Items
Every gap requiring human action before this fact sheet can be approved/distributed:
- [{{open_item_type}}] {{open_item}} — action: {{required_action}} {{open_item_citation}}

## Sources
Deduplicated citations backing every asserted figure and disclosure in this fact sheet:
- {{citation}}

---
Handoff: route the assembled `factsheet_id` + manifest to the fund's product / marketing owner;
performance figures come from `performance-attribution-builder`, exposures from
`portfolio-exposure-analyzer`, and narrative commentary from `fund-commentary-drafter`. This
skill assembles only — performance verification, compliance/marketing review, registered-principal
approval, and external distribution are separate, human-owned steps.
