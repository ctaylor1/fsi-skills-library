# Independent conduct replay against repaired methods

Replay status: **PARTIAL**. The three original conduct expectations are addressed by the repaired methods in the bounded synthetic cases. A new independently frozen long-decimal precision expectation remains unmet. The initial assessment remains **91 passed / 3 failed out of 94**; no initial input, expectation, output, command, report or hash artifact was changed.

The replay has **140 checks: 139 passed, 1 failed**. There are 18 current-method cases: the 12 unchanged original valid cases, the unchanged deliberate malformed count case, three separately amended customer unit intakes, and two independent threshold-precision challenges. All 17 valid cases passed the installed input, calculation and detached-original output CLIs. The malformed case was rejected at intake and calculation with no native output. Four newly edited current outputs claiming approval/action/narrative were rejected. Root's historical snapshots reconstructed all three original failing outputs byte for byte and passed all nine historical CLI calls.

## Original findings and honest expectation changes

| Initial finding | Current replay | Interpretation |
| --- | --- | --- |
| Known actor mismatch was suppressed by unknown classification | Unchanged `ib-partial-known-mismatch` now includes both actor mismatch and classification unknown, and overall scope comparison is false | Established mismatches survive unrelated missing facts; no access granted |
| Access-only authority missed a list-removal proposal | Unchanged `ib-access-with-list-proposal` now has `proposed list changes are outside supplied list-change authority` and false scope comparison | Proposed list changes receive separate authority review; no list changed |
| Repeat-event numerator divided by unique-customer denominator | Unchanged original intake has no typed units and now withholds harm rate, coverage and threshold; separately amended intake with numerator `events` and denominator/population `unique-customers` also withholds them | Missing units are not inferred from prose. The amended mixed-unit case demonstrates unsupported metric withholding under the new contract |

The original realistic and unknown/zero customer inputs also omit typed units. Their new pre-run expectations explicitly require valid partial intake with all metrics withheld. Their initial positive numeric expectations are not silently rewritten or credited as passing. Three separately named `*-units-amended` intakes add an explicit synthetic supplemental source and exactly mapped claims for `population_unit`, `numerator_unit`, and `denominator_unit`.

Every amendment has its own `amendment.json`, `raw-facts.json`, input, pre-run expectations, output and run record. Grounding retains the original unique-customer numerator/denominator definitions and count facts; repeated-event numerator remains explicitly `events`. The supplements are newly supplied synthetic assertions, remain unverified, and are not represented as authenticated institutional source evidence. Existing count, threshold, barrier and definition claims remain unchanged; new request/object IDs distinguish the amended requests.

With explicit `unique-customers` units, the realistic positive rates are restored: ALL harm 3%, coverage 80%; vulnerable harm 15%, coverage 50%; both exceed the supplied 2% criterion. Known zero harms remain observed zero, zero/unknown denominators stay null, missing vulnerability remains null, and missing SWITCHERS and overlapping cohort limitations remain visible. A mixed event/customer intake conservatively withholds both harm and coverage under the current supported-metric contract.

ABC replay retains the 2.5 compensation ratio, actual service discrepancy, diligence/government-link issues and counterevidence without payment approval or guilt. Currency mismatch, zero/unknown benchmark and conflicting official-link facts remain withheld. The unrounded ABC boundary 1.0000000000005 still exceeds supplied limit 1 despite display `1.000000000000`.

Investigation replay retains source chronology, competing explanations and unresolved contradiction; unknown polarity and post-receipt event chronology remain excluded from hypothesis support. The interview plan stays within the supplied mandate, the personal-device proposal stays outside it, and no collection/contact/adjudication occurs.

## New remaining numerical finding

The short-decimal pilot passes: one harmed customer of three observed has displayed rate `0.3333333333333333`; exact 1/3 exceeds the supplied decimal criterion `0.3333333333333333`, so criterion false is correct.

The independently frozen `customer-long-decimal-threshold` case instead supplies the JSON numeric literal **0.33333333333333333334**, identically in the consequential threshold claim and its source fact. Mathematically, exact 1/3 is less than this finite decimal, so the criterion should be true if that precision is supported. If the precision is unsupported, the tool should explicitly reject or withhold it.

All three installed CLIs return zero. The native output instead reports threshold `0.3333333333333333` and `within_supplied_harm_criterion=false`. Python's float JSON parsing silently shortens the decimal before `Fraction(Decimal(str(threshold_rate)))` compares it. Exact ratio comparison cannot recover the original supplied decimal lexeme once it has been shortened. The claim/source values shorten identically, so exact detached reconstruction and claim consistency also pass.

Failed independent check: **`long_decimal_lexeme_preserved`**. Evidence is in `customer-long-decimal-threshold/`, including the original input bytes with the numeric literal, pre-run raw facts and expectations, original CLI stdout/stderr, run record and hashes. This is a supplied-number precision limitation, not a legal or professional finding. No package repairs were performed by this evaluator.

## Preservation, commands and reproducibility

- `pre-run-manifest.json` freezes the 17 main replay inputs/expectations and all four current package file hashes before calls. The long-decimal case separately freezes its input/expectations and script hashes before its calls.
- `run-manifest.json` records every main current-method and historical command, working directory, return code and output hash. `customer-long-decimal-threshold/run-record.json` records the supplemental challenge commands and expected/actual comparison.
- `method-snapshot/` contains 32 runtime script copies. `method-snapshot-record.json` confirms each copied script matches the frozen current-method replay hash. These snapshots preserve the replay method even if root later repairs the live package.
- Main replay package hashes remained stable during execution; every initial artifact hash was unchanged. Initial assessment state and initial failure outputs remain intact.
- `assessment.json` records all 140 expected/actual checks and the one remaining failure. `artifact-hashes.json` indexes replay artifact SHA256 values.

Every case's `run-record.json` has exact argv and shell replay text. For the remaining numerical case, the original installed commands were:

```sh
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/customer-conduct-outcomes-reviewer/scripts/validate_input.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/replay/customer-long-decimal-threshold/input.json
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/customer-conduct-outcomes-reviewer/scripts/calculate_or_transform.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/replay/customer-long-decimal-threshold/input.json
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/compliance-financial-crime/customer-conduct-outcomes-reviewer/scripts/validate_output.py /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/replay/customer-long-decimal-threshold/output.json --input /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/replay/customer-long-decimal-threshold/input.json
```

Historical replay substitutes the recorded snapshot script path for the live package path. The snapshots for the initial three failures are under `docs/compliance-financial-crime/phase2-validation/initial-implementation/`; the replay repaired-method snapshots are under this report's `method-snapshot/` directory.

To recompute the independent assessment of retained replay outputs without changing or re-running initial artifacts:

```sh
python3 -B /Users/taylor/DevRepo/Skills/fsi-skills-library/docs/compliance-financial-crime/phase2-validation/forward-conduct/replay/assess_replay.py
```

This is bounded synthetic/offline CLI and replay evidence. It establishes no source authentication, legal applicability, institutional authority, investigation independence, privilege, professional acceptance, causal harm, live execution capability, receiver compatibility or production readiness. Source facts and the new unit supplement remain supplied-unverified. No access, list, payment, contact, device, discipline, complaint, external messaging, commit, shared-resource or catalog action was performed.
