# Handoffs

- `payment-provider-evaluator`: supply candidate options, segment/method scope, mandatory requirements, gaps and evidence IDs.
- `payment-economics-modeler`: supply participant perspective, expected demand, current costs, explicit adoption/displacement assumptions.
- `payment-integration-readiness-reviewer`: supply chosen draft design, responsibility map, acceptance/test criteria and open issues.
- `payment-lifecycle-diagnoser`: supply existing payment identifiers, ordered states and evidence before any retry discussion.

Each handoff preserves request ID, as-of date, jurisdiction, participant, source IDs, explicit units/currency and every unresolved issue. Translate to the receiving package native schema and run its native input validator. A valid handoff is not evidence that target inputs are complete. No handoff carries authority, clears a mandatory gate or repeats execution. For licensed legal applicability, third-party-risk acceptance or unavailable adjacent workflows, return an explicit capability/evidence gap and accountable human owner.
