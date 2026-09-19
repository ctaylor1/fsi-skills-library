# Reserve measures and retired runner migration

This package owns P&C volume-weighted and simple-average chain-ladder indications.
Paid latest diagonals are paid loss, and `ultimate - paid` is `total_unpaid`, which includes
case outstanding. An incurred latest diagonal is `reported_incurred`, and
`ultimate - reported_incurred` is the indicated `ibnr` measure. Never relabel paid total
unpaid as IBNR without separately reconciled case outstanding. These are method indications,
not selected/booked reserves. Reconcile paid/incurred, loss/expense, gross/net, currency/unit,
origin and valuation bases with the reviewing actuary before use.

The old model-runner's useful volume-weighted method now uses the same engine here. Its
WC paid example is preserved as `evals/files/paid_runner_example.json`, including 12/24/36/48
month ages. The native schema is in `scripts/validate_input.py`.

For old matrix input, run `python scripts/migrate_paid_triangle.py legacy.json metadata.json`.
Metadata must explicitly supply valuation_date, currency, unit and source_ref. The adapter
preserves original inputs and assumptions, rejects internal gaps/duplicate origins, and
validates the resulting native input. It does not guess missing metadata. Then run native
input validation, calculation and output validation. No old-package import is needed.

Counts are supplied estimates, not developed ultimate counts. Severity/frequency are meaningful
only with a stated compatible count/exposure basis; keep that limitation visible. Minimum/maximum
link-ratio ranges are sensitivity checks, not statistical confidence intervals. Independent
actuarial model validation and professional acceptance remain outstanding.
