# Raw-source to native-input mapping

| Native field | Raw basis |
|---|---|
| Request and history transactions | PAYMENT-LEDGER exact identity and decimal amounts; final transaction is already settled |
| authority | AUTHORITY exact scope, approval, dates and limit |
| history_review.complete | Explicit payments desk attestation, not inferred from row count |
| seven gates | CONTROL-REVIEW explicit reviewed statuses |
| Closure balances/reconciliation/obligations | CLOSURE; zero is evidenced, empty obligations explicit |
| reopen_triggers | CLOSURE trigger retained; absent owner/routing represented by null and an open issue |

Source registry paths and SHA-256 values bind each native source_ref to the exact raw artifact. Source_ref/version values are synthetic identifiers; hashes establish file identity, not truth. Missing amounts remain null. No example, evaluation, golden answer, or prior audit was read to design this case.
