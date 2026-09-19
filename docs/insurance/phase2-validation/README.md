# Insurance Phase 2 validation — 2026-09-18

Implementation and bounded local verification complete. The domain contains 40
packages: 23 retained from Phase 1 and 17 new operating foundations. The live catalog
contains 271 packages, including concurrent Payments Phase 3 additions. This record
does not claim actuarial/legal acceptance, production source access or deployment
readiness. See [scope and package inventory](../PHASE2-IMPLEMENTATION.md).

## Executed checks

| Check | Observed result | Retained evidence |
| --- | --- | --- |
| Insurance executable package checks | 197 passed, 0 failed | [Full log](selftests-insurance.log) |
| Whole-library executable package checks | 1,329 passed, 0 failed | [Full log](selftests-all.log), [exit status](selftests-all-status.json) |
| Insurance shared/route/native integration methods | 31 passed | [Log](tests-insurance.log) |
| All repository test methods | 344 passed | [Log](tests-all.log), [exit status](tests-all-status.json) |
| Structure, catalog handoffs, router/migrations | 271 packages; 0 errors/warnings; 0 dangling references | [Exact results](structural-handoff-bundle-checks.json) |
| Shared insurance resources | 40 contract references/helpers and 17 foundation bundles; no drift | [Exact results](structural-handoff-bundle-checks.json) |
| Scoped E9/F lint and whitespace | Passed | [Lint log](lint-insurance.log), final-verification.json |
| Fresh frozen inputs against final packages | 20 cases, 60 native CLI checks, 0 failures; no input hash changes | [Replay summary](final-replay/summary.json) |
| Final outputs versus independent reviewed results | All 20 JSON outputs exactly equal | [Comparison](final-independent-output-comparison.json) |

The package commands invoke nested test suites. There are 412 insurance package test
methods, including 258 in the 17 new packages; see [method counts](package-method-counts.json).
Do not add these to command counts as separate independent evaluations. Tests use
Python 3.14 with the project environment's PyYAML and Ruff. Metadata regeneration,
standalone execution for every new package, both native receiver chains, invalid
receiver dependencies, scope transitions, future sources and resealed output
tampering are covered by the insurance repository tests.

The library retains its established `compatibility` frontmatter field. Generic
skill-creator quick validation rejects that field; the repository validator accepts
the library's declared format. This mismatch is not represented as a passing generic
compatibility check.

## Independent forward evaluation

Three separate agents authored fresh synthetic practitioner requests and raw
evidence, then mapped them to native interfaces. They did not use packaged tests,
goldens or fixtures to construct the cases. They wrote practitioner responses and
checked business meaning separately from the scripts' successful self-validation.

| Stream | Baseline coverage | Findings and final review |
| --- | --- | --- |
| [Product, rate and claims](forward/claims/REVIEW.md) | Six packages | Rate and financial arithmetic matched independent expectations. Closure wrongly accepted missing reopening ownership and blank trigger entries. Root repaired the method; the same evaluator replayed unchanged baseline/complete/blank inputs and verified the defect resolved. |
| [Policy, billing and distribution](forward/operations/REVIEW.md) | Six packages | Stale requested policy value appeared as current before value; report reconciliation incorrectly required underwriting-limit basis. [Independent replay](forward/operations/after-repair/REVIEW.md) verifies both repairs and schema clarifications: 52/52 expectations pass, with all original evidence unchanged. |
| [Life and ceded reinsurance](forward/life/README.md) | Five packages | 26/26 arithmetic comparisons passed. Same-day servicing valuation restriction needed explicit documentation and a date-specific gap. [Independent replay](forward/life-after-repair/README.md) verifies the clarification and unchanged arithmetic; a separately sourced same-day variant remains distinct from the prior-day original. |

Seventeen baseline cases plus two closure variants and one service variant comprise
the final 20-case replay. Repair authors and evaluators remained separate. No
repaired input was rewritten to make it pass. Original wrong outputs remain part
of the evidence trail. A successful input/output validator only establishes native
self-consistency: the reviewers found three wrong or misleading domain outputs
that those validators initially accepted.

These are bounded agent evaluations with authored narrative interpretation, not a
held-out model benchmark or proof that every prose-to-JSON extraction is correct.
Planned natural-language cases in package eval manifests remain marked not-run.
No production records, customer decisions, filings, notices, binding or payments
were performed. Source and professional acceptance gates remain as described in
[source governance](../SOURCE-GOVERNANCE.md).

## Preservation and replay

[forward-cases.json](forward-cases.json) identifies every retained native input and
its frozen hash. [preservation-manifest.json](preservation-manifest.json) maps original
temporary paths to repository copies. Original logs and audit scripts retain their
original absolute paths as historical evidence. Full duplicated package snapshots
were omitted; the relevant original domain methods/rules and source hashes were
retained for diagnosis. Historical snapshot indices may consequently list files
not copied here; the preservation manifest explicitly records those omissions.

Use the portable repository runner with a **new** destination to reproduce final
native behavior without overwriting evidence:

```sh
python tools/run_insurance_phase2_forward.py --output /tmp/insurance-phase2-replay-new
```

The runner verifies frozen input hashes, invokes each real native input/calculation/
output script and records package hashes and no-action boundaries. It does not
rerun the independent agent's prose reasoning or promote native validation to
professional acceptance. Raw source locations inside frozen JSON retain their
original paths; scripts consume supplied evidence fields and do not fetch those
paths. The matching raw packets are retained alongside the inputs.

[Phase 1 baseline comparison](phase1-baseline-change-review.json) identifies the
intentional existing-router/four-handoff-document changes; original insurance domain
computation scripts and the Phase 1 shared contract remain unchanged. Historical
Phase 1 results have not been overwritten. source-hashes.json binds the final
implementation; artifact-hashes.json and final-verification.json record final
evidence readback. Hashes prove content identity, not evidence authenticity.

Remaining implementation work begins with Phase 3 analytical and specialist depth
in [the roadmap](../IMPLEMENTATION-PLAN.md).
