# Request contract

Common envelope: `schema_version: wealth-p0-v1`, `request_id`, `household_id`, ISO `as_of`, `engagement: {capacity: advisory|brokerage|private-bank|trust, jurisdiction: US}`, and source rows `{source_id, reference, owner, as_of, valid_until}`. Sources must cover the request date and use unique IDs. A supplied user request can be recorded as a local request reference; this is routing provenance, not substantiation for later financial claims.

Add `intents`, a nonempty distinct list from the route map. Unknown intents remain in `unrouted_intents`; known actions such as trade, transfer, account-opening, send, crm-write, legal-determination and place-hold are flagged for human handling. Invalid envelopes fail; valid requests with unsupported intents return needs-data.

See the synthetic [fixture](../evals/files/request.json). Output includes the common draft envelope, preserved input snapshot, ordered requested steps, target input requirements, unrouted intents and handoff context. Complete input hashes bind artifact lineage but authenticate neither the request nor the reviewer.

For P1/P2/P3 and any request with upstream evidence, supply `unresolved_issues: [{code, message, source_ids}]` and `upstream_artifact_ids: [id, ...]`. Unknown or missing issue citations reject; issue contents are retained in findings and handoff context. The lists are optional only for backward compatibility with standalone P0 routing requests that have no upstream artifact. Identifiers are lineage references, not authenticated approvals; inspect and validate each originating artifact independently. Output steps include `target_category` and `requested_modes` for explicit schema preparation.

P2 book routing also preserves book_id and scope_type when supplied. Inspect the full per-household context in the originating book artifact before mapping a task into a household package. The router does not batch, resolve household identities or infer consent.

P3 inputs additionally preserve scope_type with family_id or trust_id. Subject fields must be nonempty and agree with the exact reserved marker. Output target_scope is family-group or trust respectively. Scope metadata describes the reviewed case; it cannot authenticate authority, relationship, participation, entitlement or audience consent. Do not place unrelated subject IDs in the routing header as if they were interchangeable identities.
