# Raw-source to native-input mapping

| Native field | Raw basis |
|---|---|
| Position paid/outstanding by indemnity/expense | LEDGER exact balances and gross-direct USD/date |
| REPAIR/CONTESTED future amounts | ESTIMATE additional unpaid amounts; not existing case plus future |
| REPAIR recovery | ESTIMATE separately identified 4,500 |
| CONTESTED recovery | null because ESTIMATE explicitly unknown; not zero |
| scenario assumptions | ESTIMATE conditional narratives |

Source registry paths and SHA-256 values bind each native source_ref to the exact raw artifact. Source_ref/version values are synthetic identifiers; hashes establish file identity, not truth. Missing amounts remain null. No example, evaluation, golden answer, or prior audit was read to design this case.
