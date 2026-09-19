# Wealth P0 validation record

Historical P0 verification on 2026-09-16, before the subsequent P1 changes. See [P1 validation](P1-VALIDATION.md) for current working-tree results. This records implementation verification, not institutional acceptance or production certification. Scope and migration: [P0 implementation](P0-IMPLEMENTATION.md).

## Final checks

| Check | Observed result |
| --- | --- |
| Package/spec validation | 225 packages; 0 errors, 0 warnings |
| Catalog/package reconciliation | 225 unique catalog names match 225 package directories; 14 wealth packages |
| Handoff-name validation | 0 dangling references across 225 packages |
| Canonical evidence helper | Seven bundled copies match byte for byte |
| Repository P0 tests | 11 passed: evidence contract, source dates/types, complete input binding, catalog rename/addition persistence, provisional refresh, metadata reproduction and package correspondence |
| Whole-library executable evaluations | **982 passed, 0 failed**; includes 43 P0 evaluation commands |
| P0 domain regressions | **127 passed**, executed inside the 43 P0 commands; these are not additional evaluation commands |
| Ruff | Passed for `tools shared skills`, with `--select E4,E7,E9,F --ignore E401,E702,E731,E741` |
| Working diff | `git diff --check` passed |

The validation environment used a temporary virtual environment with PyYAML 6.0.3 and Ruff 0.16.8. No production credentials, client data, live systems or external actions were involved. Existing untracked `temp/` reference material was excluded.

| P0 package | Executable evaluation commands | Domain regression tests |
| --- | ---: | ---: |
| Client discovery | 6 | 9 |
| Household reconciliation | 4 | 11 |
| Onboarding | 5 | 25 |
| Risk profile | 5 | 12 |
| Recommendation evidence | 6 | 19 |
| Investor protection | 5 | 26 |
| Client review | 5 | 10 |
| Advisor follow-up | 5 | 10 |
| Router | 2 | 5 |
| **Total** | **43** | **127** |

Tests check known numerical results, explicit unknowns, stale/future evidence, subject/capacity mismatches, missing citations, substantive output, tampering and action boundaries. Passing an output-reconstruction test alone does not establish that the shared calculation is correct; numerical and independently constructed scenarios supplement it.

## Independent scenario review

Three agents reviewed packages written by other authors. The coordinator separately exercised discovery/review/follow-up variants it did not author. Temporary synthetic inputs and outputs were inspected; the reusable regression fixtures remain in the packages. These were bounded agent walkthroughs and deterministic scenario runs, not repeated multi-model or professional-quality benchmarking.

| Scenario | Observed behavior and resulting change |
| --- | --- |
| Joint household, duplicate bank statements, fractional outside ownership, mortgage, missing account and conflicting valuations | Reconciliation counted the shared bank once ($60,000), included 25% of outside brokerage ($50,000), and retained a $180,000 mortgage. Missing/conflicting accounts stayed excluded. Partial assets $110,000, liabilities $180,000 and net worth −$70,000 were correct. Router selected only discovery, reconciliation and onboarding. 24 independent checks passed. |
| Dual-registrant retirement rollover with growth appetite and a near-term withdrawal need | Risk profile retained all six dimensions, identified an $80,000 liquidity shortfall and willingness/capacity conflicts, and assigned no rating. Recommendation evidence required rollover and retirement-applicability records. Review exposed the need to carry substantive upstream concerns explicitly; required `unresolved_issues` now retain citations and artifact provenance and force needs-data even when assessment says documented. |
| Older client establishing a trust account with incomplete authority/identity evidence and a proposed large withdrawal | Both outputs remained needs-data and required human review. Review found that one missing applicability entry hid other known specialist gaps; fixed so KYC and sanctions gaps remain visible. It also found proposed activity counted as executed outflow; explicit lifecycle now separates a $120,000 proposal from $3,200 of executed outflow. Both corrected scenarios were rerun and inspected. |
| Discovery with uncollected estate evidence and an unquantified education goal | Output preserved the open goal without inventing amount/date, retained the estate evidence gap and stayed needs-data. |
| Client review with incomplete holdings detail | Output retained the value tie-out break and marked the review non-packageable. |
| Meeting follow-up with an unassigned due date and an uncited communication point | Output retained the household, attendees, drafted content and specific gaps, stayed needs-data and performed no send or CRM write. Its readiness validator intentionally returned nonzero. |

## Interpretation and remaining limits

- Common-envelope validators can accept a structurally valid needs-data artifact. Follow-up's output validator is a **readiness gate** and deliberately rejects incomplete drafts; its nonzero result in the scenario above is the expected control behavior.
- Recommendation review verifies structured evidence and declared issues, not the meaning or truth of free text. An agent/human must inspect sources and import all unresolved concerns. The required list cannot prove that no concern was intentionally omitted.
- Source owners, policy versions, review dates and approval references are supplied metadata. The scripts do not authenticate them or authorize any action. Input hashes and reconstruction detect inconsistent edits, not a consistently rewritten input/output pair; production must retain an independently protected original.
- Router handoffs require explicit mapping and target validation. The compact handoff context is not a lossless transfer of every upstream artifact or finding; retain the full request and carry those items as instructed. No automatic multi-skill executor was built.
- Senior screening can flag benign third-party assistance under a conservative supplied configuration. Institutional calibration and human assessment of benign explanations remain necessary; a screen is not evidence of exploitation or legal hold eligibility.
- Natural-language trigger, routing and safety cases without executable commands remain evaluation specifications. The full automated runner does not execute them as model tests.
- The skill-creator generic quick validator rejected the repository's existing `compatibility` frontmatter field. The repository validator explicitly supports and validates that field; the generic helper result is not counted as a pass.
- The external source workbook was unavailable. Approved merge/rename behavior was tested with synthetic catalog rows, current-catalog regeneration and package metadata reconciliation; no claim is made that the workbook itself was updated.

Professional SME/compliance acceptance, authenticated source integration, operational access/audit/retention controls and deployment-specific behavioral evaluation remain release gates. The five non-P0 wealth packages were not substantively hardened by this work.
