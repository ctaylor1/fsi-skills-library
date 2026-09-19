# Forward findings: implemented fixes and unchanged-input replay

Implemented only inside `skills/insurance/catastrophe-exposure-monitor` and `skills/insurance/insurance-data-reconciler`. Shared contract files, catalog, and root documents were not edited by this agent. Existing in-progress changes and final renamed package paths were read before edits.

## Result

- C1: unavailable or incomplete exposure evidence no longer creates numeric zero zone/TIV observations. The missing-exposure fixture now has no evaluated metrics, two retained unknown alerts, severity Unknown, and not_evaluable evaluation.
- C2: `current_evidence` records snapshot completeness separately from the overall prior-alert review. A complete no-exposure snapshot still supports the measured zero zone clear. Its unevaluated prior model alert now adds an unresolved issue, makes the overall result/artifact partial, degrades confidence, and yields severity Unknown. No zero event-model estimate is invented.
- D1: duplicate findings now retain every member's supplied value, basis, side and source reference. Standalone validation rejects missing duplicate-member evidence or citation coverage that disagrees with the retained observations.
- D2: group-level basis checks inspect every current/prior member even when duplicates exist. The combined fixture now reports both duplicate and not_comparable, retaining three observations and withholding all arithmetic. Definition-baseline checks inspect all current rows instead of only the first.

Instructions, domain/source rules and package changelogs explain the new output behavior. Positive output goldens were regenerated for the reconciliation packet and both CAT configurations.

## Validation evidence

- Targeted regressions: CAT 11 tests and reconciliation 9 tests pass (20 total; seven new tests beyond the initial 7+6).
- All 11 executable manifest evaluations pass their expected exit and output assertions, including intentionally failing negative-output controls. These manifest runs include the 20 regression tests; they are not 20 additional independent model evaluations.
- Eight unchanged independent forward inputs were replayed from the original `runs/` folder. All 32 input/calculation/output/input-bound validation stages exit 0. Input files are byte-identical to the initial runs; hashes are in `summary.json`.
- Seven independent result assertions verify the four findings, preserved zone-clear semantics, unchanged baseline arithmetic and continued withholding of incomplete model totals; see `independent-verification.json`.
- Ruff F checks pass for both packages' scripts.

Commands:

```text
/tmp/fsi-p0-venv/bin/python skills/insurance/catastrophe-exposure-monitor/scripts/test_regressions.py
/tmp/fsi-p0-venv/bin/python skills/insurance/insurance-data-reconciler/scripts/test_regressions.py
/tmp/fsi-p0-venv/bin/python /tmp/refresh-insurance-phase1-data-cat.py
/tmp/fsi-p0-venv/bin/python /tmp/insurance-cat-data-forward-20260918/replay_current.py
/tmp/fsi-p0-venv/bin/ruff check skills/insurance/catastrophe-exposure-monitor/scripts skills/insurance/insurance-data-reconciler/scripts --select F
```

The replay script retains exact commands, working directories, exits, stdout and stderr per case and manifest evaluation. Original before-results remain in `../runs/`; after-results are in `runs/`; `summary.json` compares their important states. `current-package-hashes.json` and `packages/` preserve the tested after snapshot.

## Remaining bounded limitations

A complete portfolio wholly outside a footprint can establish zero zone exposure, but the helper intentionally does not derive a zero event-model result from it. Prior event-model alerts therefore remain unknown until there is an appropriate explicit observation or a separately defined disposition method. The new overall partial status makes this clear.

A complete-empty portfolio is still conservatively unknown by the existing package contract; this change does not establish empty-feed authenticity. Partial nonempty exposure rows may still produce observed subtotals under degraded run status. Threshold policy, source assertions, geocoding, model science and external system-of-record truth remain outside this deterministic helper.

Reconciliation now exposes independent duplicate and basis conflicts but does not choose an authoritative row, convert currencies, map paid to incurred loss, or correct a source. The supplied definition identifiers carry the economic meaning; their truth is not authenticated. Group-level mismatch evidence does not promise exhaustive semantic discovery.

These are bounded synthetic simulations and local regression results, not human professional acceptance, scientific model validation or production-readiness certification.
