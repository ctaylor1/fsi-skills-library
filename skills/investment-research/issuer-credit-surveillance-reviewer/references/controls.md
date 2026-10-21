# Controls and review boundary

## Executable controls

All public entrypoints require the explicit live schema and reject legacy requests/packets with a controlled migration error. No legacy fallback or bypass flag exists. Current selftests use the supported analytical contract; retained legacy fixtures are rejection cases.

Input validation rejects invalid shapes, non-finite values, numeric booleans and future reported periods. Comparable financial context, explicit source/subject/time permissions, quote observation contents, registry versions/blocks, dated instrument mapping and supplied current-age policy constrain the calculation. See [the schema](phase2-schema.md) for the exact conditions and affected unavailable measures.

Output validation requires the separately retained original and reconstructs the entire result, including complete canonical input hash. Added/changed/removed output fields, embedded originals or substituted inputs fail. `source_truth` remains `unverified`; method/software validity grants no authority. Native output cannot carry unchecked additional narrative.

## Partial evidence and escalation

A faithful `partial` output can pass reconstruction while its unresolved issues and review gates stay open. Missing dependent metrics and spread comparisons remain null; no widening alert is emitted for a withheld comparison. Common source-permission/cutoff failure can withhold the whole projection. Ratings remain reported-only, thesis unchanged and position action none.

## Declared institutional controls

Source classifications, permissions, evidence contents, identity/mapping records and supplied context are assertions. The package does not authenticate providers/people, verify licenses, retrieve original documents, enforce institutional information barriers or determine professional/legal acceptance. Institutions own source access, MNPI restrictions, retention and review/approval. No delivery, transaction, credit approval, publication or system-of-record write is bound.

Historical source/artifacts are preserved evidence, not a live compatibility mode. Migration creates a new reviewed request and output; it must not invent observation times, mappings, financial periods or source facts.
