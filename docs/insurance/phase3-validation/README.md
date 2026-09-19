# Insurance Phase 3 validation — 2026-09-18

Implementation and bounded local verification complete. The domain contains 61 packages: 40 retained from
Phase 2 and 21 new specialist workflows. See [scope and inventory](../PHASE3-IMPLEMENTATION.md).
This record separates software checks, independent synthetic case interpretation,
professional acceptance and deployment readiness.

## Executed checks

| Check | Observed result | Evidence |
| --- | --- | --- |
| Insurance executable package checks | 308 passed, 0 failed | [Log](selftests-insurance.log) |
| Whole-library executable package checks | 1,517 passed, 0 failed | [Log](selftests-all.log), [exit status](selftests-all-status.json) |
| Insurance contract, route and native integration methods | 37 passed | [Log](tests-insurance.log) |
| All repository test methods | 362 passed | [Log](tests-all.log), [exit status](tests-all-status.json) |
| Structure, catalog handoffs and insurance routes/migrations | 296 packages; 0 errors/warnings; 0 dangling references | [Exact checks](structural-handoff-bundle-checks.json) |
| Insurance shared bundles | 61 contract helpers/references and 38 foundation bundles; no drift | [Exact checks](structural-handoff-bundle-checks.json) |
| Scoped E9/F lint and whitespace | Passed | [Lint](lint-insurance.log), [final verification](final-verification.json) |
| Final frozen-input replay | 46 inputs, 138 command checks, 0 unexpected failures; all 46 JSON results match independently reviewed outputs | [Summary](final-replay/summary.json) |

The current global total includes concurrent Payments Phase 4 work. Insurance
package commands invoke 754 test methods, including 342 in the new packages;
[method counts](package-method-counts.json) record the inventory. Those methods
are nested within commands, not additional independent evaluations. The project
environment uses Python 3.14 with PyYAML and Ruff. The
[pre-repair sweep](before-benefit-repair/selftests-all.log) also passed, illustrating
why domain review of fresh evidence was necessary beyond self-validation.

## Independent forward evaluation

Three independent agents constructed raw synthetic evidence and expected business
results from instructions and method/schema references before invoking native
scripts. They did not use packaged tests, evals, fixtures, goldens or prior audits
to construct their cases. Their practitioner narratives assess business meaning
separately from a successful input/output validator.

| Stream | Coverage | Observations |
| --- | --- | --- |
| [Analytics, premium audit and compensation](forward/analytics/report.md) | Seven workflows | 248 independent assertions pass. Initial audit/compensation mappings encountered fields added during concurrent authoring; original facts already supported them. Two explicit mapping supplements remain separate from the frozen originals. No new arithmetic defect was demonstrated. |
| [Actuarial, assumed reinsurance and finance](forward/actuarial/report.md) | Seven workflows | 98 numeric and 104 evidence/control comparisons pass. Three schema omissions blocked calculation: experience exit enums, assumed-reinsurer capacity/term enums and the close profile sign convention. Schemas were corrected; three mapping supplements preserve the original source facts. |
| [Claims, benefits, disputes, SIU, exposure, CAT and ORSA](forward/claims-risk/practitioner-review.md) | Seven workflows; 24 cases including adverse variants | 420 assertions pass after four unchanged-input benefit replays. Two dependent-output defects were repaired. Three separately mapped ORSA inputs address the documented reviewer-field mismatch. The Boolean-money case correctly rejects input/calculation/output with 1/1/1 exits and emits no insurance artifact. |

Interface-only supplements are new native inputs; they are never described as
unchanged-input repairs. Unsupported original tokens still produce explicit gaps
under the final implementation. Raw source packets, numerical facts and original
attempts are preserved. The analytics evaluator disclosed two checker-parser
failures and one nonmaterial handwritten expectation typo in
[reviewer corrections](forward/analytics/reviewer-corrections.md); these are not
package defects.

The separate benefit review exposed misleading dependent results despite correct
top-level needs-data states: unsupported monthly-method input still emitted daily
estimates, and incomplete offset inventories emitted zero offsets and inflated net
figures. Corrections withhold unsupported/dependent calculations, and the independent
reviewer verified both repairs on unchanged inputs. Supported gross amounts remain
visible when only offset inventory is unknown; offsets and net remain null.
Twelve added regressions cover these and related scope, evidence, date and row
dependencies. An ORSA guide also used
`reviewer` where the executable requires `reviewed_by`; the schema and separately
mapped inputs make that required identity explicit.

These are bounded agent evaluations, not a held-out model benchmark or qualified
insurance-professional signoff. Planned natural-language cases in package manifests
remain not-run. Supplied synthetic evidence does not verify live source truth,
regulatory applicability, extraction quality or institutional authority.

## Composition and preservation

Repository integration tests run every new package in standalone copies, select
all 21 installed routes, and exercise native capital-to-ORSA and pattern-to-SIU
handoffs. Missing context mappings, receiver-native errors and dropped unresolved
issues are tested. These examples require explicit reviewed field/basis mappings;
they do not constitute universal adapters or automated orchestration.

[Phase 2 baseline comparison](phase2-baseline-change-review.json) lists the intentional
router and four existing-package guide/version changes. Existing native insurance
domain calculations and the shared contract/foundation are unchanged. The older
checkpoints remain historical records. Concurrent payments work is preserved.

Package source hashes and artifact readback hashes bind this checkpoint to exact
local content. Hashes cannot establish source authenticity. Original temporary
paths in reviewer scripts/logs remain historical; matching raw packets are retained
beside their native inputs, and native tools consume supplied fields without
fetching those paths. No full duplicate package snapshots are included.

The [case manifest](forward-cases.json) contains 38 original synthetic inputs
(21 baseline workflows plus 17 adverse variants) and eight separately frozen
interface-mapping supplements. Four original benefit inputs use the independently
reviewed post-repair outputs; original wrong outputs remain in the audit stream.
Final replay includes 135 successful native commands and three expected rejections.
The resulting 45 draft artifacts plus one error payload all match reviewed JSON;
no rejection is counted as a valid insurance artifact.

Preservation manifests for [analytics](preservation-analytics.json),
[actuarial](preservation-actuarial.json) and [claims/risk](preservation-claims-risk.json)
record byte-for-byte copies and readback hashes. The portable runner uses a new
destination so retained evidence is never overwritten:

```sh
python tools/run_insurance_phase3_forward.py --output /tmp/insurance-phase3-replay-new
```

It verifies input and reviewed-output hashes, invokes actual native scripts,
checks expected exit codes and no-action boundaries, compares JSON results and
records current package hashes. It does not rerun independent prose reasoning or
promote those bounded evaluations to professional acceptance.

The library retains its established `compatibility` frontmatter field. Generic
skill-creator quick validation rejects it; repository validation accepts the
library's format. The generic rejection is retained, not counted as a passing
compatibility test.

Remaining implementation starts with Phase 4 architecture and measured automation
in [the roadmap](../IMPLEMENTATION-PLAN.md). Source and professional acceptance
remain separate as described in [source governance](../SOURCE-GOVERNANCE.md).
