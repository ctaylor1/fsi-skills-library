# Remaining findings repair validation

This checkpoint resolves the three findings from the follow-up review: live legacy
surveillance bypass, issuer-credit missingness, and capability-version drift.
[Implementation and migration](../remaining-findings-repairs-implementation.md)
records issuer credit 0.2.1, surveillance 0.4.1 and router 0.4.2.

| Check | Final result | Evidence |
|---|---|---|
| Full repository regressions | 1,441 passed | [Log](whole-library-tests.log), [commands](whole-commands.json) |
| Focused Investment Research regressions | 531 passed | [Log](focused-tests.log), [commands](focused-commands.json) |
| New regression methods | 62 passed | [Method inventory](new-regression-counts.json) |
| Isolated portable package execution | 308 checks across 44 packages passed | [Report](portable.json) |
| Metadata, specification and references | 395 packages; zero errors or warnings | [Log](skills.log) |
| Structure and all 42 native/canonical/bundled versions | Passed | [Log](structure.log), [version changes](version-delta.json) |
| Shared resources, exact manifests and indexes | Passed | [Resources](resources.log), [indexes](index.log) |
| Isolated saved-catalog rebuild | JSON and CSV byte equal | [Proof](catalog-rebuild.json) |
| Public-command before/after replay | 14 identical inputs in each run | [Before](before-repair/report.json), [after](after-repair/report.json) |
| Independent fresh skill use | 128 assertions passed; seven outputs reconstructed | [Review](forward-review/review-summary.txt), [assertions](forward-review/independent-assertion-outcomes.json), [draft](forward-review/analyst-draft.txt) |
| Preservation | 1,926 earlier phase and repair files unchanged | [Audit](preservation.json), [baseline](source-baseline.json) |

Counts overlap. New tests are included in both suites; portable checks, request
cases and independent assertions are separate inventories, not additive totals.

## Findings and regression evidence

Legacy requests are rejected at all three live public entrypoints, including through
the historical Asset Management alias. Relabeling an old request/output cannot
bypass native validation or detached-original reconstruction. Tests cover future
reported periods, undated/stale/unmapped quotes, unknown schema labels, malformed
JSON, current complete/partial behavior, original binding and output mutation.
Frozen historical code and packets remain available as historical evidence.

Issuer tests separately cover omission and explicit null for all seven nullable
financial values, unavailable debt reconciliation/inclusion/principal, genuinely
zero and signed values, nonpositive denominators and independent retained measures.
Original hashes preserve the difference between omitted and null inputs; partial
status cannot be changed to complete, missing metrics cannot be invented as zero,
and original data is never filled in by calculation.

Version tests compare all 42 installed packages to both current registries, including
stale values copied into both registries, missing fields, malformed values and native
metadata drift. Catalog changes are restricted to three package versions and four
capability rows; historical phase inventory versions remain unchanged.

The [first full-suite run](integration-whole-library-tests.log) exposed four active
Asset Management test expectations that still assumed successful legacy execution.
Their original source is preserved. Historical maturity/source assertions retain
their financial expectations and now explicitly execute frozen prior source;
current alias tests separately enforce migration and the repaired contract. The
[initial focused run](integration-focused-tests.log) passed 527 tests before those
alias integration regressions were added. Final logs above supersede neither
historical checkpoint: they record the current repaired sources.

## Independent use and readback

The independent reviewer read published skills, schemas and input fixtures only for
structure, without prior conclusions or expected golden outputs. Raw synthetic facts
and rational expectations were saved before execution. Ten request/original pairs
include five issuer cases, four surveillance cases and a received legacy intake.
Seven computed outputs remain appropriately partial for unresolved priority or
maturity coverage; two annual/interim mismatches and the legacy request reject.

Independent arithmetic gives EBITDA 96, debt 360, cash 24, interest 12, OCF 54, capex 18,
FFO 42 and a cited principal 366 less 6 carrying bridge. Supported gross/net/interest
ratios are 3.75x/3.5x/8x; free cash flow is 36 and FFO/debt is 7/60. Comparable supplied
quotes widen 44.75 bp. Missing evidence withholds dependent results while preserving
other supported measures. The review retains a minor generic diagnostic-wording
observation; no numerical or control failure was observed in this bounded exercise.

All 64 reviewed package-file hashes match current source. The complete 102-file
independent directory was copied and read back byte equal. The [copy proof](forward-review-copy-readback.json)
and run record bind the artifacts. The pre-edit manifest retains 120
original files with hashes equal to the 20,387-file dirty-checkout baseline. Earlier
control/evidence-reconciliation checkpoint indexes (522 and 444 files) were also
read back unchanged. [Source diff](changed-existing-sources.patch) compares current
edits with those originals rather than the aggregate Git diff.

## Limits

Repository gates pass. The installed auxiliary skill-creator validator still rejects
the repository's pre-existing supported `compatibility` field; [raw results](skill-creator-quick-validation.json)
are retained. Supported metadata was not removed to accommodate that allowlist.

The saved-catalog rebuild does not reconcile the external authoritative workbook.
These are supplied-data software controls, not source authentication, practitioner
or institutional acceptance. The broader blueprint's workflow acceptance, source
integration and deployment work remains separate. No external action was taken.
