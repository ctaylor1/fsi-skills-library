# Independent replay after repairs — six insurance operations workflows

Outcome: both domain defects and the reported schema usability gaps are resolved for the six frozen practitioner cases. All 18 native CLI steps returned 0. The original 32 independent expectations now pass (previously 30/32), and 20 additional repair/documentation assertions pass: 52/52 total. This is bounded synthetic forward-review evidence, not specialist, legal, live-source or deployment acceptance.

## Preservation and method

Each command reads the exact original native-input.json from its original case directory. `unchanged-input-evidence.json` records each original manifest SHA-256 and its matching before/after replay hashes. All 94 original evidence files were verified unchanged before and after replay. Original requests, raw evidence, normalizations, native outputs, validation results, practitioner memos and the first review remain intact. No repository files were edited by this reviewer.

New outputs, command arrays, exit codes, stdout/stderr, package hashes, documentation snapshots, updated practitioner memos and this report are confined to `after-repair/`. Replayed arithmetic uses the original independent Decimal expectations from raw synthetic evidence, without importing the packages' computation functions. No packaged tests, eval fixtures or golden outputs were used.

## Case results

| Case | Native CLI exits: input / calculate / output | Original → replay status | Independent outcome |
| --- | --- | --- | --- |
| Policy transaction | 0 / 0 / 0 | needs-review → needs-review | Current `before=12 Main St`, separate `requested_before=10 Main St`; conflict and concurrent endorsement remain visible |
| Premium billing | 0 / 0 / 0 | needs-review → needs-review | Result object unchanged: calculated close 150, difference -270, aged invoice 200 and unapplied cash 50 |
| Producer onboarding | 0 / 0 / 0 | needs-data → needs-data | Result object unchanged: conflicting active/suspended records and missing agency appointment remain unresolved |
| Placement | 0 / 0 / 0 | needs-data → needs-data | Result object unchanged: North total withheld, South total 11645, unsupported subjectivity unresolved |
| Delegated authority | 0 / 0 / 0 | needs-data → needs-review | Within-report difference -249.50 on USD written-premium basis; aggregate overrun 60000 and late receipt remain review exceptions |
| Life/annuity sales | 0 / 0 / 0 | needs-data → needs-data | Result object unchanged: liquidity conflict and missing evidence remain; no suitability decision |

Every replay retains approval=not_requested and execution=not_performed. None of these synthetic cases becomes ready-for-review merely because code defects were repaired.

## Findings disposition

1. **Policy before-value defect — resolved in replay.** The corrected row sources `before` from the current snapshot, preserves the contradictory request in `requested_before`, records `before_known=true` and `before_matches_request=false`, and attributes the snapshot through `policy_source_refs=[POL]` while preserving request refs `[REQ]`. The original before-value-conflict finding remains. Current implementation is `insurance-policy-transaction-packager/scripts/domain.py:118-124`.

2. **Delegated bordereau basis defect — resolved in replay.** The USD written-premium report's 94750.50 reported amount less 95000.00 control now produces -249.50, independent of insured-limit authority units. The output retains report currency, basis and period. Its status is observed-exception with late_or_overdue=true, and case status becomes needs-review because the previously spurious basis gap is removed. Aggregate remaining remains 120000; projected usage remains 2060000 against 2000000. The finding now explicitly says the excess is 60000. Current implementation is `insurance-delegated-authority-reviewer/scripts/domain.py:138-149` and `:175-193`.

3. **Schema usability gaps — resolved in inspected documentation.** Life schema now lists all 31 required consumer/product/life-or-annuity/replacement topic strings, explains topic conditions, freshness and partial scalar summaries. Policy source-map now publishes exact `pc`, `life`, `annuity` line values and explains all conflict-provenance fields. Reviewed copies are saved in each affected replay directory. These changes make the native vocabulary available without consulting fixtures or implementation.

## Boundaries

This replay exercises the six original inputs only. It does not independently exercise new optional expected/reported report-scope mismatch branches, absent/current-null policy values, or new upstream identity/future-date checks. None of the frozen inputs includes upstream artifacts; their unchanged case behavior supports absence of regressions here, not coverage of those new upstream branches.

Producer adverse-status interpretation and life scalar-summary/applicability limits remain narrative responsibilities documented in the practitioner responses. These were already disclosed boundaries, not newly discovered defects. No additional actionable defect was observed in this replay.

## Evidence

- `run-summary.json`: statuses, findings, results and comparison with original result objects.
- `unchanged-input-evidence.json`: six unchanged original input hash triplets.
- `original-evidence-verification.json`: verification of all 94 original evidence files.
- `independent-checks.json` / `check-summary.json`: 32 original and 20 supplemental assertions, 52 passed.
- Each workflow directory: input/output validation JSON, generated output, stderr files, commands/status, package source hashes, practitioner response; affected directories additionally retain reviewed schema snapshots.
- `evidence-manifest.json`: hashes of this separate replay evidence set. Content hashes do not authenticate source truth or confer professional acceptance.
