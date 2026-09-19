Draft billing reconciliation — FWD-OPS-BILLING, 2026-09-18

Synthetic account AC-72 / policy P-72; August 2026, USD gross premium receivable. Result: needs-review. Opening 1000.00 plus invoice 600.00, less receipts 700.00 and 650.00 and credit 100.00, with receipt R-2 and its full 200.00 reversal netting to zero, produces 150.00. The reported close is 420.00, a calculated-minus-reported difference of -270.00. [CTL, LEDGER]

OLD-1 has 200.00 outstanding and was 47 days overdue at the August 31 period end. NEW-1 is fully allocated and has zero outstanding. Receipt R-3 has 50.00 unapplied; do not assign it to OLD-1 without allocation evidence. Invoice receivable 200.00 less the separate unapplied 50.00 equals the calculated account balance of 150.00. [OPEN, ALLOC, LEDGER]

Billing finance should investigate the 270.00 control discrepancy and obtain an authorized allocation instruction for the 50.00 remainder. The package establishes no coverage lapse, collection decision, posting authority or cancellation right. A gl-reconciler handoff would need the actual GL account/control extract, period and native ledger mapping; none was supplied.

Evidence record: native-output.json. Source passages: raw-source.json. Source-to-native mapping: normalization.md. Input SHA-256: 0e86e2cc7a369aec7b2a1f52799c0dda22f9911cd912acb31194f41b99073a79.

Synthetic offline review only; not professional or deployment acceptance.

After-repair replay uses the unchanged original native input; identity evidence is ../unchanged-input-evidence.json.
