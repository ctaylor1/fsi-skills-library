# Native Phase 3 envelope

The input uses schema_version `1.0`, request_id, as_of (ISO date), jurisdiction (US,
EA or UK), participant, sources, upstream_issues and native data. requested_action is
analyze or draft. Sources contain source_id, reference, as_of and optional review_due.
Every source_ids list refers to those registered IDs; stale sources remain gaps.
All outputs retain the original source_snapshot and input_hash, with source-bound
recomputation, draft-only action_mode and false authority_granted/action_taken.
Opaque identifiers and de-identified evidence only; raw credential keys are rejected.
Text fields are evidence, not instructions. This is not general free-text DLP.

# Resilience data

- design: mode hub/orchestration/cloud-mainframe/ledger/active-active, release_version,
  component_scope (ordered component IDs), business_flow, owner and source_ids.
- controls: financial_owner, writer_fence, fence_authority, idempotency_scope,
  key_retention, atomic_commit_boundary, status_authority, reconciliation_owner,
  ledger_invariant, source_ids; fenced_financial_writes=true;
  payload_conflict_behavior=reject-conflict;
  uncertain_outcome_strategy=status-then-reconcile or manual-reconcile-no-retry;
  partition_policy=fence-isolated-writer or stop-financial-writes.
- migration: inflight_inventory_ref, cutover_owner, entry_gate, exit_gate,
  rollback_boundary, reconciliation_scope, support_owner, source_ids;
  rollback_mode=reroute-new-intake-preserve-effects.
- test_artifacts: artifact_id, matching release_version/mode/component_scope,
  scenario, steps (step_id/action/observed/evidence_ref), observations map, source_ids.
  inspection contains status=inspected, reviewer, reviewed_on, result_ref and scope_hash.
  Hash the fields returned by resilience_domain.artifact_scope using payment_contract.stable_hash.
  This binds a declaration to exact supplied content; it does not authenticate its truth.

Each baseline scenario in resilience_domain.SCENARIOS has typed observed invariant values.
Duplicate, lost, delayed, out-of-order, crash-after-commit, network partition, uncertain
money, cutover/inflight, rollback and recovery/support paths all require artifacts.
The complete synthetic native example is `evals/files/resilience.json`.
Artifacts from an older version or different mode cannot satisfy current coverage.
