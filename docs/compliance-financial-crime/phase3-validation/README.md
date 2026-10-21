# Phase3 bounded verification — 2026-10-04

Implementation and bounded software verification are complete for S3 screening
controls, M1 scenario design, M2 monitoring effectiveness and T2 case QA. All 36 target
jobs now have native methods; CFC has 38 packages including its router and 41 declared
intents. These checks establish supplied-evidence behavior and reconstruction, not
source truth, legal/practitioner acceptance, independent assurance or deployment.

| Executed check | Verified result | Evidence / scope |
| --- | --- | --- |
| Complete repository suite | 804 tests passed | [Complete snapshot log](final/repository-tests-complete-snapshot.log); frozen source plus required archived AM replay inputs and independently updated Wealth version expectation |
| Whole-library executable evaluations | 2,142 passed, 0 failed | [Evaluation log](final/library-evaluations.log); first frozen 10,116-file runtime/repository snapshot |
| Final CFC actual native integration | 38 tests passed; includes 12 Phase3 tests | [All-phase CFC log](final/cfc-all-phases-final.log); final metadata/catalog alignment and two actual-validator projection pairs |
| Final isolated packages | 40 packages, 267 command checks passed | [Report](final/portable-final-results.json); each package copied alone, no sibling imports or repository PYTHONPATH |
| Focused native regressions inside isolated commands | 932 tests; 211 across the four new packages | Included in command counts; S3=89, M1=27, M2=29, T2=66. Do not add these as independent command checks |
| Current structural metadata | 364 packages; 0 errors, 0 warnings | [Current checks](final/current-check-results.json); combined checkout includes nine unrelated concurrent additions |
| Routing, ownership, references and pins | 0 errors; 0 dangling references; all CFC resource pins match | Current checks; 41 intents and all four new primary owners |
| Catalog regeneration | Idempotent, 364 installed/registered packages across 15 categories | [Idempotence](final/catalog-idempotence.json); new metadata preserves owner/classification/jurisdiction/version/recertification without defaults |
| Preservation | 2,849 protected baseline files unchanged | [Audit](final/preservation-audit.json); original CFC packages, privacy/CM consumers, Foundation 2.0, Phase1/2 archives and Phase2 scope/migration records |

Counts from different commands overlap. In particular, the final 38 CFC tests include
cases already present in the 804-test repository run; the final metadata regression
was added afterward. The native methods and fixtures did not change in that metadata
alignment. Final isolated checks and all-phase CFC tests were repeated afterward.
Whole-library checks describe their frozen snapshot; concurrent unrelated domains
continue changing in this shared checkout. No claim of a permanently unchanged whole
library is made. The preservation audit explicitly records outside-phase changes
rather than rolling them back or claiming their authorship.

Source records: [First snapshot](final/runtime-source-snapshot.json),
[complete replay-data snapshot](final/complete-repository-source-snapshot.json) and
[final 977-file CFC snapshot](final/final-cfc-source-snapshot.json). Final CFC source
bytes match both the saved snapshot and checkout at completion, excluding ignored
cache artifacts. Native runtime is Python 3.10+ standard library. Author-time repository
validation used the existing temporary Python environment with PyYAML 6.0.3 and
jsonschema 4.26.0; no package runtime requires them.

## Independent fresh evidence and repaired findings

Evaluators wrote raw intakes and expectations before execution, retained initial
results, and independently replayed repaired methods. Original cases, expectations,
source excerpts, method snapshots and adapter/setup failures remain saved.

- [Screening/design evidence](forward-detection/FINDINGS.md): 29 meaningful final cases
  (13 screening, 16 design). Screening has 13 strict matches; design has 15 strict matches
  and one stronger safe intake rejection. Twelve original design setup/scope failures
  are retained separately. A pre-window list-load SLA breach now preserves eligible
  detection counts and fails the supplied lag criterion. Missing/null/future/unmapped
  engine evidence now withholds a scenario proposal; an unrelated benchmark cannot
  substitute. A separately predeclared unknown-lag-limit case keeps counts and withholds
  comparison.
- [Effectiveness/QA evidence](forward-effectiveness/after-repair-replay-findings.json):
  the initial final matrix contains 22 independent scenarios, plus 6 tamper and 2
  missing-original rejections. All three prior findings replay correctly on unchanged
  raw inputs. Supported minutes survive unknown cost and supported cost survives unknown
  minutes. A known unavailable required exhibit yields a completeness failure; dependent
  content criteria remain unknown and the overall QA threshold remains withheld.
- [Projection evidence](forward-projection/amended-results.json): 18 fresh amended checks
  pass after an independent review found both pairs could hide an unrelated embedded
  subject behind the review ID. Scenario/engine/population/identity/version links and
  single-case/upstream-original-hash links now bind the native subject. The original
  cross-subject cases reject. Original normal cases with unsupported namespace, cutoff
  or upstream-version evidence also reject; separately amended synthetic evidence
  supplies the newly explicit conditions. Original expectations are not relabeled as
  passes. Two actual CLI builds/verifications and detached tamper/duplicate-key checks
  are included. Source authenticity and semantic sufficiency remain human-review tasks.

Author notes and original portable runs are retained in [screening](screening-notes.md),
[monitoring](monitoring-notes.md) and [case QA](case-quality-notes.md).
The pre-repair screening package, monitoring/QA domains and projection method snapshots
retain their hashes. Repairs did not change original complete/partial golden fixtures.

## Verification limitations and initial failures

The first repository snapshot omitted two archived AM independent-replay data folders,
causing 11 test errors, and captured a concurrent Wealth version expectation before its
update, causing one failure. [The initial log](final/repository-tests.log) remains;
no CFC method was changed for these failures. The complete snapshot adds 106 archived
files and the independently updated expectation; all 804 tests then pass.

A final catalog regression exposed four mismatches before declarative metadata
alignment: catalog defaults did not retain supplied owner/jurisdiction/version fields.
[Initial regression log](final/phase3-integration-before-metadata-alignment.log) is
preserved; the final 12 Phase3 tests pass. Scenario design's archetype/pattern/action
metadata now follows the repository's Draft & package taxonomy. Runtime/domain
calculation code and original fixtures remain unchanged by this metadata correction.

[System skill-creator utility results](final/skill-creator-results.json) pass S3/T2
and reject M1/M2 only because that local utility's allowlist omits top-level
`compatibility`. The repository validator accepts this optional field; no malformed
runtime value or runtime dependency was found. This validator mismatch is recorded,
not presented as a successful check or a deployment guarantee.

The primary-source review is [recorded separately](SOURCE-REVIEW.md). Approved current
institutional/legal/method packs, independent source/label authentication, actual
professional appointment/independence, model narrative quality, enterprise access,
operational resilience exercises, configuration/rollback acceptance, external workbook
reconciliation and production acceptance remain open. Phase4 is pending. No commit,
push, merge, release, filing, external delivery or live operational action occurred.
