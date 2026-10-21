# Independent platform modernization forward exercise

Reviewer: independent agent that authored the AM data adapter, not this platform adapter. Date: 2026-10-04.

The exercise constructs a new two-lot fund ABOR migration directly from the documented native contracts. It does not read package fixtures or goldens as expected outcomes. The expected lot differences, inclusive tolerance, total architecture cost and chronology relationships are independently stated in `evaluate.py`. Original requests, resulting outputs and detached validation results are retained in this folder. These are synthetic records and have no institution or client identity.

## Initial outcome

Fourteen scenarios ran through the real native CLI; twelve met their expectations. A balanced packet remained a draft ready for human review. Opposite sub-cent breaks did not net away, tolerance was inclusive, missing expected grain blocked, wrong lots failed, RTO comparisons retained exact precision, and source/shared-output tampering failed. Accepted exceptions remained unresolved. Existing recovery and gate chronology controls worked.

Two scenarios require correction:

1. `delta-before-rehearsal-request.json`: the Oct1–2 rehearsal declares new writes, but its supposedly passed delta replay is dated Sep1. The output still reports `evidence-ready-for-human-review` and no issues. The native method should tie the replay observation to the relevant completed rehearsal and its gate review before treating rollback coverage as evidenced.
2. `closure-after-gates-request.json`: the only exception is declared closed Oct4, while all human gates were reviewed Oct3. The output still reports `evidence-ready-for-human-review` and no issues. Gates assessing the batch cannot certify a subsequently observed closure without a fresh review or explicit unresolved status.

`report-initial.json` preserves the original 14-case results. `report.json` is the most recent rerun. Re-run with `python3 -B docs/asset-management/phase3-validation/independent-platform/evaluate.py`.

## Practitioner assessment and limits

The entrypoint and reference contract make the two native schemas and their separate owners clear. The method preserves book/account/security/lot/date/unit/currency grain, declared policy thresholds and source versions rather than inferring mapping or accounting authority. Output is useful for an owner-facing migration packet and exposes exact per-grain differences. Explicit coverage of all seven mapped/excluded platform roles helps avoid silent system-boundary gaps.

The packet remains supplied evidence. Snapshot digests do not authenticate files; named reviewer strings do not prove their authority; passing gates do not authorize migration. No production connection or fund update occurred. This exercise validates native software behavior and practitioner task execution with synthetic evidence; it does not establish production readiness, source truth, real entitlement integration or broad model behavior quality.
