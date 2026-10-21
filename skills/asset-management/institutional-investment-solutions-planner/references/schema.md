# Native contract

Required common fields: request_id, object_id, as_of, knowledge_cutoff, currency (one ISO-style currency), audience=internal-review, sources[{source_ref,version,as_of,known_at}]. Source ids are unique. Optional source permitted_audiences, valid_from, valid_to, expires_at and approval_status constrain eligibility. Each business row/source reference must resolve. Sources known after knowledge_cutoff reject the request. Dates use YYYY-MM-DD. All financial facts are supplied declarations, not authenticated extraction. Retain original input separately; native output forbids source_input.

Numeric inputs: finite decimal strings recommended; <=38 coefficient digits, exponent and adjusted exponent +/-38, <=256 literal characters. Arithmetic uses a private precision256 Decimal context; ratios explicitly round to12 places. No infinities, boolean amounts or implicit zero filling. Keep jobs bounded (<=100,000 rows per collection); split larger populations with stable identifiers and separately reconciled totals. Unknown value=null produces a gap or explicit unsupported operation. Every source must be permissioned for the internal reviewer. Numeric results and classifications remain draft only.

## Domain fields

institutional_constraints{objective,governance_owner,source_ref,maximum_illiquid_fraction,permitted_delegated_actions[]}; liabilities[{liability_id,due_date,amount,source_ref}]; candidates[{candidate_id,total_assets,illiquid_assets,delegated_actions[],source_ref,liquidity_availability[{available_date,amount,source_ref}]}]. Availability amounts are incremental, not cumulative; consolidate each date first. All candidates use the same request currency and liability universe. Past-due liabilities require separate reconciliation; unknown amounts withhold coverage.

## Output

The common envelope records request/object/dates/currency, method id and version, audience, draft=true, action_taken=false, human_review_required=true, delivery_status=not-delivered, source_assurance=supplied-unverified, unresolved_issues, limitations, source_refs and input_hash. results contains the bounded domain findings and calculations described in [method](domain-rules.md). It never embeds the original request.

Source snapshot as_of cannot exceed the review as_of. Forward scenario periods and contractual maturity dates may be future, but the assumptions/terms source must already be available at the declared cutoff. Expired or unregistered row evidence is retained as a gap with dependent arithmetic withheld.

Referenced evidence explicitly excluding internal-review rejects the entire request with a generic audience-restriction error before domain identifiers, units, events or findings are emitted. This applies to nested prior/threshold/contract references as well as primary rows. Expired or unregistered evidence remains a review gap with dependent calculations withheld.

Actual dated observations admitted to a calculation or chronology must be no later than review as_of, knowledge_cutoff, and that observation source's known_at. The bound applies to experiment/split and feature dates, dated monitoring current/prior/liquidity observations and included events, and booked capital activity. Existing excluded or unsupported evidence stays withheld. Source-date declarations are checked; historical truth is not authenticated. Future scenario periods, liability/availability schedules and contractual maturity dates are assumptions or obligations, not completed events, and remain allowed.
# Phase 4 extension

`extension: liability-real-assets` selects a separate [dated liability and real-asset contract](liability-real-assets.md). Omitted extension retains the original schema below. Unknown extensions or mixing extension inputs with legacy candidate fields fail.
