# Phase 3 T2 — case quality reviewer implementation and bounded verification

Implemented 2026-10-04 in `skills/compliance-financial-crime/financial-crime-case-quality-reviewer`.
Native object: `financial_crime_case_quality_review`; method:
`case-criterion-source-and-reasoning-review/1.0`. The package supports operational QA and
second-line monitoring workpaper review. It records supplied independence evidence while
statutory independent testing, internal audit and model validation remain distinct owner methods.

## Delivered behavior

- Exact source-bound mandate, legal profile/version, authority, reviewer, native case context,
  upstream IDs/versions, period, population/sample and versioned criteria.
- Five explicit criterion methods: exhibit completeness, event/predecessor chronology, specific
  reasoning/material concern/counterevidence/contradiction linkage, proposed disposition linkage,
  and versioned tool/model/prompt/output factual source faithfulness with named human review.
- Duplicate/malformed native identity and context changes fail intake. Null substantive facts
  remain valid partial inputs. Unknown/untested cases are never passes; partial cases retain
  known exceptions while remaining outside complete-case proportion denominators.
- Complete observed case proportions require compatible population/sample/criteria, dates,
  profile and sampling rationale. Exact ratios are retained; exact decimal thresholds compare
  integer ratios without binary float or Decimal context rounding. No population inference.
- Source-specific audience/classification control includes authorized_fiu-only SAR-restricted
  native output; mixed restricted sources need an explicitly reviewed adapter. No external
  projection, raw source embedding, filing, case closure, reportability/guilt, privilege,
  reputation assessment, assurance opinion or automated decision is implemented.
- Native outputs require exact detached-original reconstruction; edited fields, additional
  narrative, changed originals and action/approval claims fail validation.

## Measured checks

The 29-file package includes five byte-identical pinned shared resources. The local foundation
contract remains `compliance-foundation/2.0` unchanged; native code uses Python 3.10+ standard
library and no sibling imports. All six frozen JSON fixtures were reopened and all manifest
hashes verified. Complete fixture: 10 observed criterion passes across two cases, 0/2 observed
case exceptions. Partial fixture retains source-bound authority/sample gaps and inherited issues.

From a package-only copy at `/private/tmp/cfc-phase3-case-quality-isolated`:

- `python3 -B scripts/test_phase3.py`: **66 tests passed**.
- `python3 -B scripts/run_evals.py`: **10/10 standard executable evaluations passed**; the
  evaluation harness also runs the same 66 tests, so these are not another independent test set.
- System skill-creator validation passed using `/tmp/cfc-phase2-venv/bin/python`.
- Repository package validator: zero errors; one expected pending-catalog warning at the time
  of package creation. Root integration owns catalog updates and final repository checks.

Exact commands, exit codes, stdout/stderr and limits are preserved under `case-quality/`.
The default author-time Python lacked PyYAML; an existing validation environment supplied it.
No package runtime dependency was added. Package-only isolation established offline portability.

## Source and professional limits

Primary FFIEC, FinCEN, OFAC and DOJ conceptual references were accessed on 2026-10-04
America/New_York / 2026-10-05 UTC. Source publication/section revision dates are recorded separately;
exact publication days remain unknown where the primary source gives only a section year or month.
The references are not a comprehensive institution-approved legal pack.

The method checks explicit evidence linkage, structured chronology and exact source consistency.
It does not semantically certify human reasoning, authenticate sources/reviewer identity/authority,
validate model behavior, issue assurance, or prove legal applicability, professional/institutional
acceptance or production readiness. All supplied facts and proposed narratives remain unverified.
No external communication, live action, commit, push, merge or release was performed by this work.
Only the new T2 package and its assigned validation notes/evidence were written by this subtask.

## Independent forward finding and narrow repair

The independent evaluator supplied `/tmp/cfc-phase3-forward-effectiveness/T2-scoped-exhibit-missing.json`
with an exactly source-bound required exhibit whose availability is false. The initial method
retained a mechanical exception but classified the completeness criterion unknown because the
observation's content-link check also required availability. This erased a known failure count.
Initial method/tests/manifest bytes and hashes are preserved under `case-quality/initial-*` and
`pre-independent-repair-snapshot.json` before the repair.

The narrow correction classifies a known unavailable required exhibit as a completeness failure.
Dependent chronology/reasoning/disposition/tool checks still remain unknown when their content
is unavailable; partial case denominators and threshold withholding remain intact. The regression
now requires exactly one known criterion failure and the dependent unknowns. The same 66 tests and
10 executable evaluations pass in `/private/tmp/cfc-phase3-case-quality-repaired-isolated`; exact
post-repair logs, manifest readback and original-input hash are in `post-forward-repair-result.json`.
Complete and partial frozen goldens remain byte-unchanged. Local replay of the independent raw
intake now reports pass5/fail1/unknown4. This local developer replay is separate from the independent
evaluator's original-intake recheck, which the parent coordinates. No detection package was edited.
