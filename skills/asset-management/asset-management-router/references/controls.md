# Routing controls

## Before routing

Require a nonempty request ID, real `YYYY-MM-DD` date, nonempty declared-intent list
and nonempty subject type/ID. Unknown intents, impossible dates, malformed inventory,
nonfinite numeric values and unsupported action labels fail native input validation.
The supplied inventory must use exact canonical package names. The router does not
infer installation from paths, display labels, mode names or planned directory entries.

Separate fund NAV, portfolio value, manager fee revenue, investor capital accounts and
listed-manager equity valuation. Confirm which professional owns the job. Review-only
scope never grants authority to trade, release NAV, post books or send a report.

## Route and method controls

Check subject compatibility before using any candidate. A scope mismatch returns
`needs_scope_clarification`; an execute request returns `execution_not_supported`.
Neither launches a workflow. Out-of-domain candidates identify the owning library;
company IT inventory has no AM candidate. Missing installation is recorded on every
primary and supporting reference independently, without changing method support.

Planned methods remain `planned_capability` even when declared installed. Institutional
manager diligence and institutional RFP requests remain `partial_capability_gap`
because their current methods implement narrower household review and approved-answer
matching. Review supporting methods independently; their presence does not complete
the missing primary workflow.

## Integrity and delivery

Run `validate_output.py OUTPUT --input ORIGINAL`. Reconstruction binds all native
fields to the complete original request, rejects altered route/status/authority fields
and rejects unexpected native fields. Do not attach free-form professional conclusions
to the native object; prepare separately reviewed narrative using the output template.
Hashes and deterministic checks do not authenticate sources or human approval.

Every result has `action_taken: false`, `authority_granted: false`,
`human_review_required: true`, `delivery_status: not-delivered`; every candidate has
`execution_authorized: false` and every plan has `launch_performed: false`.
Keep unresolved issues unchanged. A separate handoff must validate the producer output,
receiver-native schema, exact field mapping and inherited issues under the handoff
contract. Human investment, compliance, accounting and external-delivery approval remain
outside these scripts.

## Evidence of testing

The synthetic eval matrix independently declares the expected primary/status for all
24 intents, compares supporting references and checks installation annotations,
deduplication, scope mismatch, invalid inputs and execution refusal. Stored goldens are
also validated against original inputs, including negative mutations. These checks test
routing contracts; they do not test natural-language intent recognition, source truth,
enterprise installation or acceptance of the downstream professional workflow.
