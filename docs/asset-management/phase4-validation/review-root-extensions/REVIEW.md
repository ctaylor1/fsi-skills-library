# Independent Phase 4 forward review of root-owned extensions

Date: 2026-10-04. Reviewer authored the separate transition, financing and hedge work, not these three extensions. Inputs here were built from new synthetic source records and the exposed contracts; package golden answers were not used as expected results. Initial emitted artifacts and initial source copies/hashes were saved before repairs.

## Initial observations

The first 12 fresh cases reproduced four defects, retained in `initial-findings.json` with their original inputs/outputs:

1. **Currency attribution — same-currency FX:** a nonzero USD/USD FX return produced a clean draft and artificial FX effects. The method now requires an uppercase currency code, a real base currency and zero FX return for the base currency.
2. **Currency attribution — hedge chronology:** a realized whole-period hedge contribution was accepted from a source known before the period ended. The period end now passes the actual-event chronology check against the hedge source.
3. **Walk-forward — observation configuration:** a test sample tagged with another strategy version was compounded as if it belonged to the requested experiment. Every train/test observation now binds strategy_version, protocol_version, execution_model_version and selected_trial_id exactly to the request; missing or mismatched pins fail.
4. **Walk-forward — retrospective predeclaration:** the model accepted a protocol/selection fixed after test outcomes while labeling the trial limit predeclared. New required actual dates protocol_frozen_on and selection_decided_on use protocol_source_ref and must be strictly before the first test day under this day-grain method. Later/same-day evidence withholds aggregate performance; missing/malformed dates fail.

These controls establish consistency of supplied evidence, not source truth, independence or actual historical experiment conduct.

## Independent calculations and outcomes after repairs

All 12 original forward expectations passed after repair. Five additional ETF engine cases passed, yielding **17 independent forward assertions**. Valid emitted outputs were separately reconstructed by each package's actual output validator using its detached original input; details are in `after-repair-validation.json`.

- Currency example: portfolio return 0.0484; benchmark 0.04125; active return 0.00715. Domestic and foreign beginning weights, local returns, FX interaction and supplied hedge contributions were calculated independently from the source records.
- Walk-forward example: net returns 0.0194 and −0.0107 compound to 0.00849242. Distinct training/test events, delisted historical universe membership, cost drag and temporal feature availability are explicit.
- ETF example: EUR bond face 2000 at clean 101 plus accrued 1 percent gives local dirty value 2040; FX 1.1 gives 2244 USD. Eight equity shares at 25 add 200; cash 56 reconciles to 2500 NAV value. Two units plus fee 7 give indicative AP cash 119.
- ETF supplied-engine extension: 50 derivative contracts at separately supplied 3 USD per contract add 150. A rehashed request for another derivative, mismatched units, absent engine and benchmark discrepancy were challenged using the actual native scripts. Dependent totals were withheld or rejected as appropriate; no derivative pricer ran.

The repair added 18 meaningful native regressions across the root packages. Their current Phase 4 tests pass: attribution 15, walk-forward 21, ETF 17. ETF gained a fresh engine-bound input/output fixture and two declared input/output validation commands. Existing no-extension interfaces and prior-phase fixtures were not changed.

The root-authored practitioner document, template and changelog files were left untouched. They must reflect the new walk-forward dates and observation pins, and attribution currency/hedge-chronology constraints. Real financial data, institution approval, live models, professional acceptance and production deployment were not evaluated.
