# Independent Phase 3 S3 / M1 forward findings

Raw evidence packets and expectations were written before native runs; complete inputs were built
from documented shapes with new source records, IDs and facts. Synthetic evidence stays supplied
and unverified. Native detached reconstruction passed for every computed result. No action or
professional-acceptance claim was emitted. Reviewed package files were not edited by this evaluator.

## S3 — known pre-window list-update SLA breach suppresses observed detection counts

Raw intake: `s3-list-update-delay.json`; original result:
`s3-list-update-delay.output.json`. Independent expectation: `criterion-false`, unchanged.

The loaded/expected versions and entries match. Effective time is October1 09:00Z, loaded time
09:20Z, and the review starts October2 12:00Z. The 1,200-second update lag exceeds the supplied
600-second criterion, but the correct snapshot was loaded before the entire observed window.
All four engine observations use this exact list/configuration/engine and source-separated labels.
Manual observed sample: TP2, FP1, TN1, FN0.

The original result correctly retains `within_supplied_update_lag_limit=false`. It also sets
list coverage false, then renders all four test results ineligible, counts all confusion classes
as zero and returns overall criteria null. The known historical SLA failure should remain a
failed criterion without erasing independently observable detection outcomes under the correct
pre-window snapshot. Coverage and failure are conflated at original domain.py line293 (`lag_ok
is True` inside coverage), then list coverage is required for measurement at line352.

This is one method issue. The parent assigned a narrow author repair; original raw intake,
expectation, output and original method hashes remain preserved for independent replay.

## M1 — absent or unsupported scoped engine evidence does not block configuration proposal

Raw intake: `m1-benchmark-only-scope-adapted.json`; original result:
`m1-benchmark-only-scope-adapted.output.json`. Independent expectation: `proposal-withheld`.

After removing all bank engine observations while retaining an explicitly incomparable external
benchmark, the native result reports `proposal_prerequisites_consistent=true`, no material blockers,
`status=draft-for-human-review` and a populated `proposed_engine_configuration`. Documentation
requires scoped engine workpapers and keeps benchmark references distinct from engine observations.
An empty loop vacuously passes the prerequisite instead of establishing a gap.

Four independently prepared extensions confirm the same missing gate: a future engine workpaper,
null substantive observation, null engine version and absent exact observation fact locator all
leave the proposal present and prerequisite flag true. Foundation issues set needs-evidence, but
the method's material blockers remain empty. Evidence is in `engine-extension-result.json` and
matching raw/output files. These are four manifestations of one gating flaw at original M1
`domain.py` lines131–144: resolution adds issues but not proposal blockers.

## Safe boundaries and setup correction

S3 correctly handles missing receipts, overlapping feed/case identities, fine-precision FP
criteria, hindsight/unknown labels, source access, native scope, changed list snapshot and exact
source-value divergence. Its baseline manually matches TP2/FP1/TN1/FN0 and a FP ratio1/2.

The initial M1 packet used a review ID separate from the scenario ID. Intake rejected it because
M1 native object ID must equal its source-bound scenario ID. All original raw packets and initial
errors are retained. A separate before-run adapter changes only actual native/context IDs to the
scenario identity; intentional context mismatch remains mismatched. Expectations are unchanged.
This setup correction is not evidence of a method defect.

Corrected M1 retains explicit non-execution and blocks ambiguous links, overlapping holdout item
or dataset identity, fine-precision total mismatch, gross/net basis mismatch, unknown population
grain, SAR/source access and duplicate identities. Engine-population mismatch stops intake,
which is stronger than the evaluator's withheld-proposal expectation and is accepted as a safe
boundary. No raw expectations were rewritten after observing output.

All exact commands, exit codes, outputs, detached validation, action flags and initial expectations
are preserved in result.json, corrected-result.json and engine-extension-result.json. These are
bounded independent synthetic cases, not practitioner acceptance, legal applicability, source
truth or live-engine effectiveness. Parent/author owns repair; evaluator makes no package edits.

## Independent after-repair replay

After stable author notices, the evaluator reran unchanged original S3 raw intakes and all
original expectations, saving after results separately. **13/13 S3 cases passed**: the original
12 cases plus one separately declared-before-run unknown SLA limit. Pre-window lag breach now
retains TP2/FP1/TN1/FN0 and returns the failed overall criterion; unknown SLA limit retains those
same counts with comparison withheld. Valid baseline and all scope/access/source guards remain.
Evidence: `after-s3-repair/result.json`. Original source packets/expectations/results hash-unchanged.

M1 **16 meaningful corrected/extended cases passed the required boundaries**: 15 exactly match
unchanged independent expectations; the engine-population mismatch is rejected at intake, a safe
stronger boundary. Missing/null/future/unmapped engine evidence now blocks prerequisite consistency
and configuration proposals, while valid baseline still emits only a non-actioning draft. The 12
original native-scope setup failures were separately replayed and retained, not counted as valid
substantive cases. Evidence: `after-m1-repair/result.json`. All original inputs, expectations,
results and corrected adapter packets remain hash-unchanged.

Across final meaningful replay, 29 cases were exercised (13 S3 / 16 M1), with exact detached
reconstruction passing for each computed output and action controls intact. The 12 replayed M1
setup failures are recorded separately. No evaluator edits were made to either detection package.
The two identified native method issues are resolved by these bounded forward cases; professional,
institutional, legal/source-authentication and production acceptance remain unestablished.
