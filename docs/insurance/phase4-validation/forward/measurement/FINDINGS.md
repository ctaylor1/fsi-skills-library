# Findings and disposition

## F1 — Documentation did not fully specify the native input contract (resolved in current docs)

The originally read schema profile paragraph (line 7 in all four packages) described required profile fields without specifying data.profile. A top-level profile produced `reviewed rule profile unavailable`, with dependent metrics null. Automation schema's requested_mode row (line 21) only said text/null; its controls rows did not enumerate the six mandatory control IDs. Initial human-assist and two meaningful controls therefore failed semantic completeness. Architecture operation row (line 48) did not state read/proposed-write, so write was rejected as a gap. These are workflow usability failures rather than unsafe arithmetic. Exact original errors and successful validation exits are in initial-run/. Runtime diagnostics and narrowly targeted implementation searches resolved nesting and enums. The parent added explicit documentation.

Schema-only mappings: profile moved to data.profile for every case; human-assist became assist; write became proposed-write. Optional data projection=null explicitly declines projection. These edits were distinct from new fictional evidence: six required tests and full proposed contracts were newly supplied in SUP-1; backlog accruals were also supplied separately, never inferred as zero. This separation prevents a success-shaped record from being mistaken for unchanged source evidence.

## F2 — Open-episode unknown amounts blocked unrelated queue measures (resolved in replay)

operations-unknown-open-cost-input.json has complete timestamps and completed-episode cost/labor. Only E2/E5, still open, lack amounts. Original native output withheld every aggregate. The broad original rule that evidence gaps withhold aggregates allowed this conservatism, but it conflicted operationally with the narrower completed-cohort cost definition and made ordinary incomplete accounting unusable. Replayed identical input now retains those source nulls, returns opening 2, arrivals 3, completed 2, cancelled 1, closing 2; mean 15 hours; nearest-rank p95 24; cost 24; labor 30; utilization .75. There is no invented value.

## F3 — License flag depended on unrelated benchmark/projection sufficiency (resolved in replay)

With an explicitly unreviewed optional projection, observed metrics were already preserved once profile mapping was fixed: 4/6 coverage and $60 reduction. The initial suspicion that projection suppressed observed results was disproved; earlier outputs were confounded by the wrong profile location. However `license_usable_for_stated_purpose` changed to false solely on missing projection inputs (and separately on temporal leakage) despite identical supplied license evidence. Repaired outputs keep the license flag true while withholding the invalid comparison or projection. This scopes the flag correctly; it remains an unauthenticated assertion check.

## F4 — Contradictory independent queue control needed explicit qualification (resolved in replay)

A closing tally of 3 conflicts with extract closing 2. Original output marked needs-review and difference -1 but retained all numeric aggregates, whereas original method prose said inventory/evidence gaps withhold aggregates. This was not silent arithmetic acceptance, but the scope of retained figures was unclear. Replayed output now adds snapshot_reconciled=false, and current draft labels all measures extract-only until Elena reconciles the discrepancy. The parent is clarifying method prose. No staffing action is authorized.

## Arithmetic and evidence outcomes

Architecture: 280+420+160=$860/month; scoped 640ms <=700ms. Imperfect mismatched workload plus unknown quote correctly null fit and total.
Automation: baseline 20 vs candidate 14 human minutes; baseline/candidate errors both 1/4 with different failed cases; candidate nonlabor $3 vs $1. Six thousand eligible annual cases free 600 capacity hours valued at $28,800, yet cash nets are -$18,000 at 0% realization and -$3,600 at 50%; no payback or pilot recommendation. Missing rework timing and failed duplicate replay correctly withhold the dependent case.
Data: 4/6 matches; baseline TP1/TN2/FP1/FN2, augmented TP2/TN2/FP1/FN1. Costs $240 vs $180 = $60 reduction. Both unmatched outcomes are retained. No representative annual projection. D1 future availability correctly blocks the benchmark.
Operations: queue conservation 2+3−2−1=2; completed 24h/6h yields mean 15h and nearest-rank p95 24h; completed cost $24 and labor 30m; unfinished ages 30h/8h; utilization 12/16=.75.

All ten repaired outputs retained byte-equivalent parsed source documents, false action_taken, true human_review_required, approval=not_requested and execution=not_performed. The 74-check audit uses original raw rows for arithmetic, not script outputs as expected values. Narrative review separately checks scope, contrary cases, unknowns and owner boundaries.

## Limitations and process disclosure

These tiny purposive fictional samples do not prove real source truth, production control behavior, representativeness, legal rights or professional acceptance. Source IDs and hashes demonstrate retention, not authenticity. The evaluator read SKILL/references/templates first, and inspected narrow runtime contract locations only after semantic failures. One broad scripts/*.py search unintentionally returned three test_domain.py profile/measurement-scope lines; no bundled fixtures or test datasets were opened or used to originate facts or expected arithmetic. This is a disclosed minor departure from the intended clean documentation-only setup. Exact original failures and derived inputs are retained rather than concealed.

No repository files were changed by this evaluator. Parent-owned repairs were evaluated through the exact-input replay, without adjusting cases to fit the repaired outputs.
