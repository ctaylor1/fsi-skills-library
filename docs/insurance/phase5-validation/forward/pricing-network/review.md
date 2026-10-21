# Independent forward-test review — 2026-10-04

Scope: fresh synthetic source-mapping cases for health-plan-pricing-reviewer and health-provider-network-reviewer. Read only package SKILL.md and schema before drafting cases; no author input fixtures, tests or domain implementation were read. Each folder contains the raw source, request, native mapping, retained-output artifact and native output validation. No package edits were made by the forward tester.

## Findings

No implementation defect was observed in these four bounded cases. They exercise source mapping and the native evaluator through the documented interface. This is an independent agent forward test, not a blind human trial, real institution acceptance, evidence authentication, licensing review or statistical quality benchmark.

- Pricing normal: 125000 paid + 10000 unpaid case + 20000 IBNR minus 5000 recoveries = 150000 incurred; /600 member months = 250 base PMPM; cumulative cost factor 1.08 and utilization factor 1 give 270 projected claims PMPM. Fixed 7200/720 plus 26 PMPM yields 36 nonpremium expense. (270+36)/(1-0.08-0.02) = 340 conditional premium PMPM; compared with 320 supplied comparable current premium gives 0.0625 renewal change. Output matched every value, remained draft and did not call the descriptive ratio statutory MLR.
- Pricing adverse: raw source explicitly withholds IBNR and does not assert zero. Native null mapped directly. Result needs-data, all derived metrics and category measures null; original facts retained.
- Network normal: three provider-site records represent two distinct clinicians. For the first member both clinicians are within 10 driving miles; for the second, only clinician A qualifies despite two qualifying sites. Output counts 2 and 1, respectively: 1 of 2 members meets the supplied two-provider threshold, fraction 0.5 below the supplied 0.75 benchmark. Result needs-review; no regulatory inadequacy or licensure conclusion was asserted.
- Network adverse: source expressly supplies only five of six required measurements and flags the missing second-member/B-CENTRAL distance. No distance or nearest-provider inference was inserted. Native result needs-data and withholds derived counts/fractions/eligibility/comparison.

All four final outputs retained source_document exactly and passed native output recomputation. Action remained false; human review remained required; approval not requested and execution not performed.

## Source clarification and current-schema replay

The initial network source narrative described per-site contract and credential evidence without spelling its exact record IDs. A distinct fictional source-author clarification supplies those exact IDs. Initial inputs/outputs remain saved; final mappings explicitly cite the supplement. This is documented source clarification and a rerun, not an unchanged-input repair or inferred professional review. It changes no statuses, dates, measurements, population, completeness facts or expected results.

After package schema tightened the accepted capacity enums, the final mappings use health-pricing-review and health-network-review. Per-case capacity-normalization.json preserves the previous native spelling and actual source review role. Raw represented party, object and professional boundaries are unchanged. All final cases were replayed against the revised runtime; current output validation passed.

## Remaining acceptance limits

No real clinical/actuarial/network specialist evaluated these outputs. Real-source authenticity, private-source access, legal/program applicability, privacy/accessibility, real-model benchmark variance and production operation remain unverified. Further tests are warranted only for new changes or new failure evidence.
