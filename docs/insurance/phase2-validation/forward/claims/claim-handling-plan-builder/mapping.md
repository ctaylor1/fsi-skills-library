# Raw-source to native-input mapping

| Native field | Raw basis |
|---|---|
| Task IDs, descriptions, owners, dates, state, dependencies | DIARY, preserved without changing the supervisor dependency graph |
| Completion evidence | ACK-731 exact supplied locator |
| Unknown T-RECOVERY owner/date | Native null, not an invented owner/deadline |
| deadline_basis | All dates explicitly service targets |

Source registry paths and SHA-256 values bind each native source_ref to the exact raw artifact. Source_ref/version values are synthetic identifiers; hashes establish file identity, not truth. Missing amounts remain null. No example, evaluation, golden answer, or prior audit was read to design this case.
