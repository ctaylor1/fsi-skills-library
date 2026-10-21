# Native input and output

Common foundation fields: request_id, object_id, as_of, knowledge_cutoff (real dates), currency (same as shared baseline), audience `internal-review`, nonempty versioned sources with source_ref/version/as_of/known_at, and unresolved_issues. Every business record has a registered source_ref. The original input remains separate from the output.

`shared_reviews.operations` contains `input`, `output`, and source_ref. Input and output are the unmodified native operations-performance-analyzer pair for the same object, as_of and currency. Every source must also be registered here with identical version/as_of and an eligible known_at. Use its native profile, context and observed episode schema; do not convert another population into this baseline by relabeling an envelope.

`services`: unique service_id; function, current_owner, target_owner, accountable_owner, backup_owner, system_of_record, population, definition_version, provider, retained_oversight_owner, escalation_route, business_calendar, time_zone; delivery_model internal/outsourced/co-sourced; criticality critical/material/standard; depends_on list of service IDs. Outsourced/co-sourced services also require audit_rights_ref, exit_plan_ref, subcontractor_register_ref. `service_inventory`, inventory_source_ref and inventory_complete are explicit source-backed declarations.

`controls`: unique control_id, service_id, maker, checker, frequency, evidence_locator, failure_route, control_version, tested_version, test_result pass/fail/not-tested, tested_on for actual tests, source_ref.

`transitions`: unique transition_id, service_id (at most once), owner, acceptance_owner, rollback_owner, rollback_runbook, training_record_ref, access_review_ref, rehearsal_result pass/fail/not-tested, rehearsed_on for observations, open_exceptions (observed nonnegative integer), source_ref.

The deterministic result lists service/control/transition gaps, dependency order, original shared operating measures and ready_for_owner_review. operating_change_authorized and staffing_change_authorized are always false. Missing facts create review gaps; malformed identities, sources or dates fail validation. Passing supplied tests establishes no actual permission or professional approval.
