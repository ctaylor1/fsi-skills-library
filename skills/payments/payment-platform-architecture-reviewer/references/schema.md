# Native request and output contract

All commands consume JSON and run locally. Input envelope: `schema_version: "1.0"`,
`request_id` (caller-provided durable work-item reference), `as_of` (YYYY-MM-DD),
`jurisdiction` (`US`, `EA`, or `UK`), `participant`, `sources`, `upstream_issues`, and
`data`. A source has `source_id`, `reference`, `as_of`, and optional `review_due`.
Use `source_ids` arrays referencing those registered IDs on all material data rows.
Missing evidence is a finding. Invalid types, unsafe actions and invented source
IDs are input errors. `requested_action` permits `analyze` or `draft` only.
An unsupported region returns `unsupported` with no jurisdiction-specific result.

The source inventory records supplied claims; it does not authenticate evidence.
A passed validator is not evidence inspection. Source review-due dates before the
analysis date create gaps. Future source dates are rejected. Raw PAN, CVV, PIN,
track data, customer secrets and payment credentials are unnecessary: use opaque
card/account/token references and synthetic or minimized business evidence.

Output contains `status` (`draft`, `needs-evidence`, `unsupported`), a retained
`source_snapshot` and `input_hash`, `result`, source-linked `findings`, `handoffs`,
upstream unresolved issues and limitations. `authority_granted` and `action_taken`
remain false. A hash establishes content lineage, never identity or approval.
Compare a saved output to separately supplied input when source binding matters.

## Architecture data

`context`: business_flow, current_constraint, target_outcome, module
(issuer/acquirer/hub/orchestration), source_ids.
`components`: component_id, role, owner, source_ids.
`data_models`: entity, identifier_fields, authoritative_component, state_values, source_ids.
`flows`: flow_id, stage, from_component, to_component, state_entity,
mutates_money (boolean), source_ids. Supported stages: initiation, authentication,
authorization, routing, capture, clearing, settlement, funding, posting,
reconciliation and servicing.

Money-changing flow objects also carry:
- idempotency: key_fields, scope, retention, atomic_enforcement,
  payload_conflict_behavior (reject-conflict/manual-review), source_ids.
- uncertain_outcome: strategy (status-then-reconcile/manual-reconcile-no-retry),
  status_authority (component ID), source_ids.
- reconciliation: source_component, target_component, partition_fields including
  legal_entity_id/account_id/currency, match_keys, owner, exception_queue, source_ids.
- posting flow: ledger_invariant, stating the balancing and reversal design.

`nfrs`: nfr_id, metric, target (finite nonnegative decimal), unit, measurement_plan,
owner, source_ids. Availability/success-rate uses percent or ratio.
`options`: option_id, description, component_changes, benefits, tradeoffs,
acceptance_evidence, source_ids. No option is automatically selected.
`migration`: phase_id, sequence integer, scope, entry_evidence, exit_evidence,
inflight_handling, financial_reconciliation, rollback_boundary, rollback_mode,
dual_financial_execution boolean, owner, source_ids.

Result: component_map, flow_edges, flow_assessments, state_authority_map,
nfr_assessments, decision_records and migration_phases. A supplied design is not
validated implementation. See [../evals/files/normal.json](../evals/files/normal.json).
