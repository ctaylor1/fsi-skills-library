# Native schema

Use common request/object identity, `as_of`, `knowledge_cutoff`, one `currency`, `audience: internal-review`, versioned sources and unresolved issues. Every transaction, interim event, conflict and option includes eligible `source_ref`. Dates are real YYYY-MM-DD; all actual events must exist by review/cutoff/source-known date. Inventories are explicit and bounded at10,000. Finite decimal strings avoid binary-input ambiguity.

`mode`: `lp-led-secondary` or `gp-led-continuation`.

`transaction`: `id`, `version`, `reviewed_by`, `currency`, `nav_date`, `materials_received_on`, `decision_deadline`, `settlement_date`, `pricing_convention: reference-nav-plus-calls-minus-distributions`, `conflicts_owner`; nonnegative integer `minimum_review_days`; nonnegative `reference_nav`; `existing_management_fee_rate` and `existing_carried_interest_rate` in[0,1]. Reference NAV is the entire LP interest under comparison, not the whole fund unless that is the actual object.

`interim_flows`: explicit list, possibly empty, unique economic-event `id`, `kind: capital-call|distribution`, actual `date`, same `currency`, `transaction_version` and nonnegative `amount`. Dates must be after reference NAV and by settlement, review and known cutoff. `flow_inventory_complete` and `inventory_source_ref` declare completeness; incomplete inventory withholds dependent cash/roll amounts.

`conflicts`: explicit list, possibly empty; unique `id`, `description`, `owner`, `status: open|resolved`. Resolved records require `resolution` and actual `resolved_on`; open conflicts remain issues.

`options`: nonempty unique `id`, same `transaction_version`/`currency`, `side_letter_treatment`, `fee_carry_basis`, `price_to_reference_nav` in[0,10], nonnegative `cash_fees`, `cash_crystallized_carry`, `new_management_fee_rate`/`new_carried_interest_rate` in[0,1], boolean `status_quo_claimed`. LP-led options use positive `sale_fraction` up to1 and cannot contain any GP-only `roll_fraction`, `roll_fees`, `roll_crystallized_carry`, `upfront_new_capital` or `new_uncalled_commitment` fields; these are rejected rather than silently ignored. GP-led options use `roll_fraction` in[0,1] and also require nonnegative `roll_fees`, `roll_crystallized_carry`, `upfront_new_capital`, `new_uncalled_commitment`; they cannot use `sale_fraction`. Cash-only GP options cannot carry roll-side fees, carry, capital or commitments.

Fee/carry amounts are supplied allocations to the specific option; no waterfall is inferred. Each output is a source-bound internal draft with separate cash/roll/retained values, fee/carry differences, timing, conflicts and no selected option. Original input is required for output reconstruction.
