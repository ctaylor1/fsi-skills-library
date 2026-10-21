# Routing method

The caller declares one or more supported intents and an actual subject. The router
does not use loose keyword matches. Invalid/duplicate intents fail validation;
incompatible subject types yield needs_scope_clarification. Missing institution,
legal entity, jurisdiction or responsibility yields needs_context.

Otherwise a planned primary yields planned_capability_gap. A missing installation
inventory yields installation_unknown; an explicitly absent primary yields
primary_not_installed. A bounded_route identifies a documented native method, not
task completion or legal applicability. Supporting planned/uninstalled methods and
unconfirmed data remain listed even when a primary route is available.

Requested approval, execution, sending, filing, restrictions or customer-state changes
yield action_requires_separate_authorization. The router does not infer that any later
approval has occurred. Context strings, source references and available_skills are
supplied declarations, not verification.

Native handoffs require actual producer/receiver validators and an explicit schema
adapter; four legacy batch/framework/time schemas remain native-only. For registered
schemas, a common packet additionally requires complete workflow context and a native
assessment date. Missing fields must be supplied from real evidence, never invented.

Phase2 registers 19 domain objects and explicit customer lifecycle/substantive modes.
Common handoffs preserve the full detached source-fact registry, knowledge cutoff,
context, classification, audience and unresolved issues. Same source/version labels
cannot substitute changed facts. Changed subjects, cross-audience disclosure and
foundation-to-legacy projection require separately reviewed adapters.
