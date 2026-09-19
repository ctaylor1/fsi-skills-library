# Native input contract

Common envelope: schema_version "1.0", request_id, as_of ISO date, jurisdiction US|EA|UK, participant, sources[] with source_id/reference/as_of/optional review_due, upstream_issues[] with code/message/optional source_ids, and data. Only analyze/draft requested_action is allowed. All amounts are nonnegative finite decimal strings or integer values; unknown values are null/omitted and remain unknown. Negative net positions are output results, not negative source transactions. Arrays must be present, including explicit empty arrays for confirmed no activity. Every native row includes source_ids registered in the envelope; primary row IDs must be unique.

`data.window_start`, `window_end`: timezone-aware ISO instants. `history_complete`: boolean.
- `accounts[]`: account_id, entity_id, currency, rail_profile_id, funding_model, snapshot_at, balance, held, source_ids. Other than US-FEDNOW/US-RTP, require funding_model_evidence. FedNow model master-account|correspondent-account; RTP prefunded-position|funding-agent-prefunded-position.
- `events[]`: event_id, economic_id, account_id, entity_id, currency, kind (inflow/outflow/settlement-obligation), certainty (firm/forecast), due_at, amount, source_ids. Distinct legs must be independently evidenced and uniquely identified; no automatic inter-account transfer is synthesized.
- `reservations[]`: reservation_id, account_id, event_id, currency, amount, source_ids. One reservation per outgoing event, amount no greater than that event; holds in accounts exclude these amounts.
- `funding_windows[]`: window_id, account_id, opens_at, closes_at, source_ids. Caller-declared actual funding access/availability windows; not derived from network customer-payment uptime.
- `stress_scenarios[]`: scenario_id (unique, not base), rationale, remove_inflow_ids[], outflow_multiplier_bps integer >=10000, source_ids.
Output: account_positions with base and stress scenario_paths, chronological available balance, minimum and peak_shortfall. Excluded inflows carry reasons. No pooling, conversion or movement is performed.

For a runnable native example, see the package evals/files/request.json. Outputs retain the original source snapshot and deterministic input hash.
