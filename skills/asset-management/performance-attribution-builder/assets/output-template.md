<!--
Performance Attribution — output template (attribution-template@0.1.0)
Draft & package deliverable. Section headers below mirror the canonical `sections` keys enforced
by scripts/validate_output.py (REQUIRED_SECTIONS). Populate every {{placeholder}} from the
assembled manifest; every segment row MUST carry its citation and every attributed row MUST tie
out (allocation + selection + interaction + currency = total). Effects are decimals; multiply by
10000 for basis points. This is a DRAFT ex-post decomposition for human review — never a
recommendation, advice, a forward-looking/guaranteed-performance claim, or a GIPS-compliance claim.
-->

# Performance Attribution (DRAFT) — {{attribution_id}}

> Draft performance-attribution analysis for human review only. It is not investment advice and
> not a recommendation; it makes no forward-looking or guaranteed-performance claim and asserts no
> GIPS compliance; the effects are an ex-post decomposition of realized return, and this draft has
> not been reviewed, approved, or delivered.

## Attribution Summary
- Attribution ID: {{attribution_id}} | Portfolio: {{portfolio_id}} | Benchmark: {{benchmark_id}}
- Period: {{period_from}} to {{period_to}} | Base currency: {{base_currency}}
- Model: {{model_family}} | Config / template version: {{config_version}} / {{template_version}}
- Build status: **draft-attribution**
- Human approval required before delivery: **yes**
- Counts: segments {{segments}} · attributed {{segments_attributed}} · needs-data {{segments_needs_data}} · open items {{open_items}} · approvals recorded {{approvals_recorded}} / outstanding {{approvals_outstanding}}

## Portfolio Benchmark
- Portfolio return: {{portfolio_return}} | Benchmark return: {{benchmark_return}} | **Active return: {{active_return}}**
- Local decomposition: portfolio-local {{portfolio_return_local}} · benchmark-local {{benchmark_return_local}} · portfolio-currency {{portfolio_currency_return}} · benchmark-currency {{benchmark_currency_return}}
- Cite: {{citations}}

## Segment Attribution
Per segment, the Brinson-Fachler effects (each row cited; each attributed row ties out):
- {{segment}} ({{currency}}) — wP {{weight_port}} / wB {{weight_bench}} (active {{active_weight}}) — allocation {{allocation}} · selection {{selection}} · interaction {{interaction}} · currency {{currency_effect}} = **total {{total}}** — status {{status}} — cite: {{citation}}
- [needs-data rows] {{segment}} — missing {{missing}} — weight unattributed until resolved — cite: {{citation}}

## Effect Totals
Firm-wide totals across attributed segments (sum to the active return):
- Allocation {{allocation_total}} · Selection {{selection_total}} · Interaction {{interaction_total}} · Currency {{currency_total}} = **Attributed {{total_attributed}}**

## Currency Attribution
Segment totals rolled up by segment currency (a reporting view of the reconciled effects):
- {{currency}}: {{currency_bucket_total}}

## Reconciliation
- Effects tie-out: attributed {{attributed_active_return}} vs active {{active_return}} — residual {{residual}} — status **{{recon_status}}**
- Book-of-record (official): portfolio bottom-up {{bottom_up_portfolio}} vs official {{official_portfolio}} (residual {{residual_portfolio}}, {{status_portfolio}}); benchmark bottom-up {{bottom_up_benchmark}} vs official {{official_benchmark}} (residual {{residual_benchmark}}, {{status_benchmark}})
- Weight coverage: sum(wP) {{sum_weight_port}} · sum(wB) {{sum_weight_bench}} · unattributed wP {{unattributed_weight_port}}

## Methodology
- Model family: {{model_family}} | Return basis: {{return_basis}}
- Interaction: {{interaction}} | Currency: {{currency_method}}
- Linking: {{linking}} | Factor attribution: {{factor_attribution}}
- Every effect is deterministic and reproducible from the cited segment inputs; the model, config,
  and template versions are recorded for audit.

## QA Checks
Deterministic tie-outs and coverage screens:
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
Handoff: to turn this attribution into portfolio-review narrative route to `fund-commentary-drafter`;
to place it in a fund fact sheet route to `fund-fact-sheet-builder`; to include it in an investment-
committee pack route to `investment-committee-memo-builder`; to assemble a client review pack route
to `client-review-preparer`. Multi-period geometric linking and factor-based attribution are out of
scope and go to the performance-measurement / quant team. This skill assembles a draft only — the
methodology sign-off, the compliance/marketing (SEC Marketing Rule) review, and any external
delivery are separate, human-owned steps.
