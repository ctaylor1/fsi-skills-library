# Raw-source to native-input mapping

| Native field | Raw basis |
|---|---|
| Period, P=4,875,000, L=2,940,000, E=3,900 | EXPERIENCE; three aligned native rows |
| Monetary units, factors, Z, C, F, K, R, V, Q | PRICING-MEMO, verbatim values, represented as decimal strings |
| alignment_reviewed and basis enums | Explicit reconciliation and convention statements in EXPERIENCE and PRICING-MEMO |

Source registry paths and SHA-256 values bind each native source_ref to the exact raw artifact. Source_ref/version values are synthetic identifiers; hashes establish file identity, not truth. Missing amounts remain null. No example, evaluation, golden answer, or prior audit was read to design this case.
