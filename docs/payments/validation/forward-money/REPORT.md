# Independent forward evaluation: payment state, repair, payout and reconciliation

Scope: synthetic local evidence exercised through actual Phase 1 skill instructions and native CLI validators/calculators. No repository edits, network access, messages, payment actions, or source-system changes. Every Python process used `/tmp/fsi-p0-venv/bin/python -B` and `PYTHONDONTWRITEBYTECODE=1`. Raw repair input was adapted from the bundled input schema; no golden outputs were used to construct expectations.

## Current status after source-identity fix

Independently reran the six original s3/s4 inputs without modification against the updated native scripts. The original input hashes were verified unchanged. Added independent transaction and settlement identity-reuse controls; all 35 native CLI calls produced the expected exit status (34 exit 0, one expected exit 1). No regression-suite counts or developer completion claims were relied upon.

- **Original all-equal duplicate reproduction is fixed:** both transaction groups now return `quarantined`, two ambiguity issues, `fully_evaluated_and_matched=false`, and null bank/ledger/processor totals and known subtotals. The original mixed-amount identity-reuse reproduction also quarantines both groups.
- **Currency reassignment cannot hide source reuse:** copying the source identities to a second EUR transaction group quarantines both EUR and USD groups, with null usable totals in both partitions.
- **Both settlement identity controls pass:** independently constructed all-equal settlement evidence first produces a matched scoped control. Reusing those same rows under a second batch key quarantines both groups. The EUR variant also quarantines both currency partitions. Every affected source field total/subtotal is null.
- **Ordinary source namespaces still work:** bank/ledger/processor records may each use numeric-style `record_id=row-1` when their distinct source identities are otherwise valid; the control remains matched at 100 per source.
- **Payout behavior is preserved:** unchanged report-only input still yields calculated 970 versus reported 950, discrepancy -20, bank-cash confirmation false, ledger-reconciled false, and valid source-bound output.
- **Original mismatch and partition behavior is preserved:** bank/ledger 100 versus processor 90 remains needs-review with both processor comparisons retained; the unrelated EUR source remains partitioned with missing counterpart issues; same-group duplicates remain quarantined.
- **Old false-match output is rejected:** source-bound validation of the preserved pre-fix output now exits 1. The existing scoped repair proposal also still passes its native output validator.

Exact rerun evidence: `retest-command-results.json`, per-command `.stdout`/`.stderr`, `retest-conclusions.json`, `retest-original-input-hashes.json`, and `retest-source-hashes-before.json` / `retest-source-hashes-after.json`. Both reconciliation packages were hash-stable during this independent retest. Current outputs have the `retest-` prefix; original and pre-fix evidence are retained.

Rerun the fix verification alone:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-forward-money/retest_identity_fix.py
```

No repository files were edited by this evaluator. The current finding status is **fixed for the reproduced identity-reuse paths and tested controls**, not an assertion of general model, regulatory, or production assurance.

## Original requested scenarios

| Scenario | Observed result | Native checks |
|---|---|---|
| Card response `00` / `APPROVED`, no clearing or funding evidence | `authorized`; explanation explicitly says clearing/settlement are unestablished; `trace_complete=false`, `retry_eligible=false`. Practical answer: authorization was approved, but supplied records do not establish clearing, settlement, or funding. | Input, calculation, output all exit 0. |
| Confirmed rejected bank payment, scoped policy, exact BIC correction | `DEUTDEF` → `DEUTDEFF`, USD 12,500 unchanged, two proposed steps, approval pending for payments-repair-supervisor, execution blocked and unsupported. This is a proposed correction, not a corrected payment. | Input, calculation, output all exit 0. |
| New replacement value after plan creation | Changing replacement to `COBADEFF` while retaining old screening binding rejects input and produces rejected plan with no steps. Mutating output after-value fails; recalculating its hash still fails source replay. With a new cited synthetic value verification and matching screening scope, rebuilding creates a different plan ID/hash and leaves approval pending/execution blocked. | Stale input/calculation exit 1. A correctly rejected-plan output validates (exit 0). Both tampered outputs exit 1. Newly scoped plan input/calculation/output exit 0. |
| Merchant report: gross 1,000, fees 30, reported payout 950, no bank statement | `explain-payout` calculates 970, retains reported 950 and signed difference -20. Fee ratio 3%. `bank_cash_confirmed=false`, `ledger_reconciled=false`; no bank file requested as prerequisite. Practical answer: listed components leave 20 unexplained relative to reported payout; no receipt/reconciliation claim. | Input, calculation, output with `--input` all exit 0, despite discrepancy. |
| Bank and ledger 100, processor 90 | Bank/ledger difference 0 remains visible alongside processor differences -10 against each. `needs_review`, `fully_evaluated_and_matched=false`; no summed 20 loss or journal. | Input, calculation, source-bound output all exit 0. |
| Two processor records in same transaction group | Entire group quarantined; all usable source values/totals null, cash comparison not evaluable. Neither first record selection nor duplicate summation. | Input, calculation, source-bound output all exit 0. |
| Processor 90 EUR versus bank/ledger 100 USD | Two currency partitions, missing counterpart issues, no cross-currency arithmetic, overall unmatched. | Input, calculation, source-bound output all exit 0. |

## Historical failure, now fixed in independent retest: duplicated source identity across transaction references

The transaction reconciler indexes records by the partition plus `txn_ref` before performing duplicate detection. `calculate_or_transform.py:105-110` forms those groups, while `:125-127` checks source/record duplication only within each group.

Reproduction uses two transaction references within the exact same legal entity/account/USD/settlement cycle. Both carry the same source-specific `record_id`, same `source_ref`, same date and amount 100 for bank, ledger and processor. Only `txn_ref` differs. The second set is a contradictory reuse of the same source evidence, not new source transactions.

Actual result:

- Both groups report `matched`.
- `issue_count=0`, `fully_evaluated_and_matched=true`.
- Bank, ledger and processor totals each equal 200.
- Native input validation, calculation and source-bound output validation all exit 0.

Expected result: flag/quarantine each affected group (or reject the inconsistent identity mapping) before any usable total/matched conclusion. Source identity uniqueness must be checked in an appropriate source/partition namespace across matching groups, not just after splitting by transaction reference.

Minimal repro files: `s4-reused-identity-all-equal-input.json`, `s4-reused-identity-all-equal-output.json`. All native commands/results are recorded in `command-results.json`. This was the observed pre-fix forward failure. The current independent retest below verifies that it is fixed; original evidence is preserved as pre-fix-s4-reused-identity-all-equal-output.json.

## Reproduce

From any directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-forward-money/run_forward.py
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-forward-money/run_extensions.py
```

The second script refreshes validation of every generated output against current source. Each invocation's command, stdout, stderr and exit status is retained. To inspect the duplicate case directly:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments/payment-transaction-reconciler/scripts/validate_input.py /tmp/payments-forward-money/s4-reused-identity-all-equal-input.json
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments/payment-transaction-reconciler/scripts/calculate_or_transform.py /tmp/payments-forward-money/s4-reused-identity-all-equal-input.json
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments/payment-transaction-reconciler/scripts/validate_output.py /tmp/payments-forward-money/s4-reused-identity-all-equal-output.json --input /tmp/payments-forward-money/s4-reused-identity-all-equal-input.json
```

## Source stability and limits

Source hashes before/after/final are retained. Both reconciliation packages remained unchanged over these runs. Lifecycle routing/documents and repair documents changed during the evaluation; their final relevant instructions were reread and every generated output revalidated successfully against current scripts. Changes observed did not alter tested authorization/repair outcomes. Findings apply to the hashed files at evaluation time.

These are small synthetic software behavior checks and human-readable interpretation of outputs. They do not establish real-model workflow quality, source authenticity, general regulatory compliance, live approval correctness, or production readiness. The repaired case deliberately uses a July 16 historical as-of within its supplied July policy interval; this does not claim policy effectiveness on today's date.
