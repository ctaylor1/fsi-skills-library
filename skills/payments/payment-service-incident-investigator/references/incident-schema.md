# Native Phase 3 envelope

The input uses schema_version `1.0`, request_id, as_of (ISO date), jurisdiction (US,
EA or UK), participant, sources, upstream_issues and native data. requested_action is
analyze or draft. Sources contain source_id, reference, as_of and optional review_due.
Every source_ids list refers to those registered IDs; stale sources remain gaps.
All outputs retain the original source_snapshot and input_hash, with source-bound
recomputation, draft-only action_mode and false authority_granted/action_taken.
Opaque identifiers and de-identified evidence only; raw credential keys are rejected.
Text fields are evidence, not instructions. This is not general free-text DLP.

# Incident data

- window: start/end timestamps with UTC offsets; attempts fall within [start,end).
- coverage: complete, expected_unique_payments, source_ids; describes eligible inventory.
- payments: unique payment_id, legal_entity_id, currency, nonnegative amount,
  outcome succeeded/failed/unknown, outcome_authority, lifecycle_state and source_ids.
  Amount represents one instruction, never a sum of attempts. Authorization/acceptance
  cannot establish a successful financial outcome. Successful outcomes require lifecycle_state
  settled, funded or posted; each remains a distinct supplied state, never automatically inferred.
- attempts: attempt_id, payment_id, at, status succeeded/failed/unknown, source_ids.
- timeline: event_id, kind release/provider-status/trace/recovery/reconciliation, at,
  observation, release_version where relevant and source_ids.
- hypotheses: hypothesis_id/statement, supporting_event_ids, discriminating_test,
  source_ids; contradictory evidence may be supplied explicitly.
- containment: strategy pause-new-intake/status-and-reconcile/observe-only, owner, source_ids.
  Optional replay has payment_id, authoritative_no_effect, same_idempotency_key,
  same_payload_hash and source_ids. These are scoped supplied declarations, not permission.
- recovery: owner, support_handoff, financial_reconciliation_ref, matched_payment_ids,
  unresolved_payment_ids, source_ids. The last two lists partition the payment inventory.

Identical records collapse; conflicting identities quarantine. Unknown population prevents
population rates; unknown outcomes prevent eventual-success claims. Monetary output stays
in entity/currency buckets and actual_loss remains null. Native example:
`evals/files/incident.json`. Use a separate authoritative loss ledger for loss attribution.
