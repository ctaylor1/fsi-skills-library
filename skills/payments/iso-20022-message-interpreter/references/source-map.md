# Normalized JSON adapter

No raw XML parser, XSD validator, live external code-set lookup, SWIFT directory, network connection, or transformation-map engine is implemented. Local JSON is the authoritative supplied input to this package; retain its parser/source provenance separately.

Every input requires full `message_type` (`family.NNN.VVV.NN`). Transaction/status profiles use normalized `group_header` with `msg_id` and `cre_dt_tm`. Transaction profiles require a nonempty `transactions` list with `end_to_end_id`, `amount: {value, currency}`, and `source: {system, ref}`. Amounts are explicit finite nonnegative decimals.

Status profiles allow transactions without amounts and/or `group_status`. Every transaction status needs `status.code` and source; group-only status uses the group message reference. The header `nb_of_txs`, when supplied to this adapter, must count the normalized records represented, not an unrelated original batch. Original-message totals must be retained separately rather than relabeled as current-report controls.

Classification-only profiles require top-level `source: {system, ref}` and do not require or manufacture transaction rows. Message names for camt.110/111/admi.024 do not imply field-level support.

Optional `mapping_profile` identifies a cited mapping (`source_ref`), positive `max_remittance_length`, and optional `charset: SWIFT-X`. Warnings apply only to that supplied profile. Optional guideline/version labels are metadata, not validation results.

Output carries the source message/hash, mode, false `schema_validated`/`scheme_validated` flags, limitations, cited findings, and per-currency totals. `raw_control_sum` is arithmetic only; it must not be reused as economic exposure across currencies.
