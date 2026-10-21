<!--
Comparable Company Analysis — output template (comps-analysis-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys
enforced by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}}
from the assembled manifest; every EV bridge, multiple, and implied value MUST carry its
citation (or, for implied values, a summary-statistic basis). This is a DRAFT cross-check for
human review — never a recommendation, rating, price target, or valuation/fairness opinion.
-->

# Comparable Company Analysis (DRAFT) — {{analysis_id}}

> Draft comparable-company analysis for human review only. It is not investment advice, not a
> research rating or price-target, and not a valuation or fairness view; the multiples and any
> implied ranges are an analytical cross-check, and this draft has not been reviewed, approved,
> or delivered.

## Analysis Summary
- Analysis ID: {{analysis_id}} | Subject: {{subject_ticker}}
- As-of (market) date: {{as_of_date}} | Currency: {{currency}} | Units: {{units}}
- Config / template version: {{config_version}} / {{template_version}}
- Peer selection criteria (versioned): {{peer_selection_criteria}}
- Build status: **draft-comps**
- Human approval required before delivery: **yes**
- Counts: peers included {{peers_included}} · excluded {{peers_excluded}} · open items {{open_items}} · approvals recorded {{approvals_recorded}} / outstanding {{approvals_outstanding}}

## Subject Company
- {{subject_ticker}} — {{subject_name}}
- Market cap: {{subject_market_cap}} | Enterprise value: {{subject_ev}} — cite: {{subject_citations}}
- LTM: revenue {{subject_ltm_revenue}} · EBITDA {{subject_ltm_ebitda}} · EBIT {{subject_ltm_ebit}} · EPS {{subject_ltm_eps}}

## Peer Set
Every included/excluded peer with a cited rationale (inclusion and exclusion are human-confirmable):
- [{{status}}] {{ticker}} — {{name}} — rationale: {{rationale_or_exclude_reason}} — cite: {{citation}}

## EV Bridges
For each company (subject + peers), the enterprise-value bridge (each component cited):
- {{ticker}}: market cap {{market_cap}} + debt {{plus_total_debt}} + preferred {{plus_preferred}} + minority {{plus_minority_interest}} − cash {{cash}} = **EV {{enterprise_value}}** — cite: {{citations}}

## Trading Multiples
Per company, per metric, with non-meaningful (nm), missing, and outlier flags:
- {{ticker}} {{is_subject_flag}} {{stale_flag}} — EV/Revenue LTM {{ev_rev_ltm}} · EV/EBITDA LTM {{ev_ebitda_ltm}} · EV/EBIT LTM {{ev_ebit_ltm}} · P/E LTM {{pe_ltm}} · EV/Revenue FY1 {{ev_rev_fy1}} · EV/EBITDA FY1 {{ev_ebitda_fy1}} — cite: {{citations}}

## Summary Statistics
Computed on meaningful, in-stats peer multiples only (subject, nm, missing, outlier, and stale-priced values excluded):
- {{metric}}: n={{n}} · min {{min}} · Q1 {{q1}} · median {{median}} · mean {{mean}} · Q3 {{q3}} · max {{max}}

## Implied Valuation (cross-check range only)
Peer statistic × subject metric → implied EV / equity / per-share. This is an analytical range for human review, NOT a target or recommendation:
- {{multiple}} @ {{basis}} ({{basis_multiple}}x) → implied EV {{implied_enterprise_value}} · implied equity {{implied_equity_value}} · implied per-share cross-check {{implied_share_price_cross_check}}

## QA Checks
Deterministic tie-outs and consistency screens:
- {{check}}: {{status}} — {{detail}}

## Open Items
Every item requiring human action before this analysis can be finalized/delivered:
- [{{open_item_type}}] {{item}} — action: {{required_action}} {{open_item_citation}}

## Approvals
Recorded:
- {{approval_type}} — {{approver_role}} — {{approval_date}} — cite: {{approval_citation}}

Outstanding (required, not yet recorded):
- {{outstanding_approval_type}} — status: outstanding

## Source Index
Deduplicated citations backing every asserted figure in this analysis:
- {{citation}}

---
Handoff: for an intrinsic cross-check route to `dcf-modeler`; for independent methodology/input
review route to `valuation-reviewer`; to place the finished page in a client deliverable route
to `investment-banking-pitch-builder`. This skill assembles a draft only — the valuation
conclusion, any recommendation, and external delivery are separate, human-owned steps.
