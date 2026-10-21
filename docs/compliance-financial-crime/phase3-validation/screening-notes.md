# Phase 3 S3 sanctions screening control evaluator

Implemented new `skills/compliance-financial-crime/sanctions-screening-control-evaluator`, version 0.1.0, reviewed 2026-10-04; recertification 2027-10-04. Existing packages, shared foundation API, catalogs/router/tools and Phase 1/2 evidence were outside this package task's edits. Root integration owns global preservation and routing/catalog acceptance.

Native object: `sanctions_screening_control_review`. Method: `supplied-screening-control-reconciliation/1.0`. Bundled helpers and contracts remain byte-identical to compliance-foundation/2.0 and native_integrity/1.0.0. The native runtime is Python 3.10+ standard library, with no sibling imports or live connectors.

## Executed verification

- 89 native unittest cases passed, including complete and partial frozen reconstruction, actual bad/tamper fixture rejection, exact decimal comparisons beyond float precision, label/observation separation, missing labels/cases/denominators, feed/list/configuration scope and chronology, access/classification/source conflicts, resilience/latency unknowns and complete observed failures, instruction-like evidence, and an actual copied-package run outside the repository.
- 9/9 executable repository-format CLI evaluations passed. One eval repeats the domain suite; repeated executions are not additional unique cases.
- System skill-creator validator passed using existing `/tmp/cfc-phase2-venv/bin/python`; repository package validator passed. Native runtime scripts require neither PyYAML nor JSON Schema libraries. Runtime compatibility is retained in string metadata because the system quick validator rejects a top-level compatibility field that the repository validator accepts.
- Two JSON Schemas passed Draft 2020-12 schema checks; four frozen complete/partial input/output artifacts passed shape validation. This check supplements exact executable native validation.

Commands, raw stdout/stderr and the bounded summary are saved in [screening validation evidence](screening/validation-summary.json). Package resource hashes are recorded in its [manifest](../../../skills/compliance-financial-crime/sanctions-screening-control-evaluator/references/package-manifest.json).

## Native meaning and limits

Reconciles screening-input IDs, feeds, fields/scripts, list snapshots/versions/entries/effective-load timing, engine/build/config/vendor evidence, and known-test/sample/control coverage. Supplied label-reference and engine-observation source records are distinct. Expected labels represent scoped test alert behavior, not sanctioned-person identity or legal ground truth. TP/FP/TN/FN sample counts remain distinct from unlabeled observations, errors, unmeasured cases and coverage. Sample rates retain integer denominators and exact fractions; comparisons use exact decimal-string rational arithmetic.

Complete coverage can coexist with a supplied observed failure. Unknown scope, engine/list/configuration evidence, latency requirements or workpapers withhold the dependent overall comparison. Operational effectiveness, legal exposure/disposition, statistical population inference and independent assurance remain unestablished. No engine or threshold tuning/execution, current-list retrieval, operational action or professional acceptance is implemented. Real-model activation and routing were not evaluated by these native checks.

## Primary-source review

Official reference material was retrieved/reviewed 2026-10-04, distinct from publication dates: [OFAC Framework](https://ofac.treasury.gov/media/16331/download?inline=), officially announced 2019-05-02; [FFIEC OFAC manual](https://bsaaml.ffiec.gov/manual/OfficeOfForeignAssetsControl/01), retrieved section date not shown; [FATF supervisory guidance](https://www.fatf-gafi.org/content/dam/fatf/documents/reports/RBA-Effective-supervision-and-enforcement.pdf), cover October 2015, Example 23; [OFAC FAQ 5](https://ofac.treasury.gov/faqs/5), original 2015-01-30/current update 2026-09-09. These support bounded control design and professional boundaries; they are not a comprehensive approved law pack or live list inventory.

## Independent forward repair

An independent raw-input review identified conflation of a known pre-window list-update SLA failure with missing list/version evidence. The original package and original forward intake/output are preserved in `screening/pre-list-lag-repair/`. The repaired method retains eligible labeled detection counts when the correct list/version/entries were effective and loaded before the review window, while the known lag breach fails the supplied overall criteria. An unknown lag requirement also preserves independently eligible detection counts and withholds the overall comparison. Two domain regressions and an executable frozen SLA-breach evaluation cover the distinction. The original six frozen fixtures remained byte-identical; the new SLA input/output are additional artifacts. See [repair evidence](screening/list-lag-repair-summary.json). The saved native totals above reflect the repaired method.
