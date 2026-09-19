# Wealth evidence contract and analysis/workflow helpers

`wealth_contract.py` is the canonical standard-library implementation of the `wealth-p0-v1` envelope. Twenty-six package-local copies are maintained by `tools/sync_wealth_contract.py`; `--check`, `tools/test_wealth_p0.py` `tools/test_wealth_p1.py`, `tools/test_wealth_p2.py` and `tools/test_wealth_p3.py` verify exact consistency. The envelope identifier is retained for compatibility; it is not a delivery-wave label.

The helper validates JSON-safe values, professional capacity, US scope, source ownership/reference/date metadata, item source IDs, input hashes and draft/no-action posture. Each package is responsible for substantive domain validation and output reconstruction. This helper authenticates nothing and never performs external actions.

All sources require `source_id`, `reference`, `owner`, `as_of`, and `valid_until`; source validity must cover request `as_of`. This is a required supplied review window, not an automatic freshness rule for every financial document. The institution must set and verify the appropriate policy. Stale registry entries are rejected; a domain-specific stale valuation or missing observation can remain an explicit needs-data finding where its package supports that state.

Outputs carry `schema_version`, `skill`, `request_id`, `household_id`, `as_of`, `engagement`, `sources`, `input_hash`, `artifact_id`, `status`, `findings`, `result`, `human_review_required: true`, `action_taken: false`, and `delivery_status: not-delivered`. Findings require a code and message; any unresolved finding makes the common status needs-data. Review-ready is structural readiness for human review, never professional approval.

Source snapshots retained by domain packages contain sensitive financial evidence. Use pseudonymous identifiers, minimum necessary fields and deployment-approved storage/retention. See [P0 implementation](../../docs/wealth-management/P0-IMPLEMENTATION.md) for migration, handoffs and release limits.

`wealth_analysis.py` contains strict decimal parsing, evidence, output-reconstruction and CLI primitives used by tax, advisory fees and wealth performance. Three bundled copies are checked by the same sync tool. Domain numeric contracts remain explicit: this helper accepts finite decimal strings or numbers, while other packages may accept only JSON numbers.

See [P1 implementation](../../docs/wealth-management/P1-IMPLEMENTATION.md) for all thirteen workflows, exact upstream-issue field mappings and the distinction between draft R4 rebalancing and separately certified execution. Neither helper imports sibling skill packages or authenticates source data.

`wealth_workflow.py` supplies shared P2/P3 policy applicability, explicit upstream-issue records, finite Decimal parsing, findings, full output reconstruction and CLI handling. Six byte-identical copies support book, prospect, lending, private-market, family-governance and trust-administration review. Its alias rejection requires explicit mapping from P1/router `unresolved_issues`; resolution needs attributed dated evidence. See [P2 implementation](../../docs/wealth-management/P2-IMPLEMENTATION.md) for subject scopes, numeric boundaries and handoff rules. Helpers preserve consistency; they do not authenticate records or prove completeness.

[P3 implementation](../../docs/wealth-management/P3-IMPLEMENTATION.md) adds explicit family-group and trust subject markers. Domain packages extend handoff_context with family_id/trust_id and reviewed actual-subject associations. The retained household_id envelope key does not make a collection or trust marker a client identity. Router findings require separate target requests for incompatible scopes.
