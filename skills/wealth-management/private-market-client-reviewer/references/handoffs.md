# Handoffs and boundaries

| Adjacent job | Direction and exact material |
| --- | --- |
| household-wealth-data-reconciler | Inbound household/account ownership, capacity, source register and unresolved conflicts. Confirm the positions/accounts inventory is complete. |
| investment-manager-due-diligence-reviewer (Asset Management) | Inbound manager report, artifact ID/input hash, reviewed date/review-by, status and substantive findings. Do not repeat team, strategy, operational, fee or liquidity due diligence here. |
| household-financial-planning-assistant | Outbound account-dated known obligations, forecast scenario, reserve assumptions, complete/unknown fields and exact source/issue context. No presumed inter-account liquidity. |
| investment-risk-profile-reviewer | Outbound illiquid exposure/NAV limits, commitments and dated funding gaps; it separately assesses willingness, capacity, liquidity and horizon evidence without a chosen risk rating. |
| investment-recommendation-evidence-reviewer | Outbound funding/NAV/eligibility/manager gaps relevant to a separately proposed recommendation. This package itself makes no recommendation. |
| wealth-performance-report-builder | Settled movements with actual dates, position/account/fund IDs and explicit household external-flow scope. Notice/forecast amounts are never actual cash flows; reconcile the target reporting perimeter and valuation dates before use. No returns are calculated here. |
| wealth-account-service-packager / authorized operations specialist | A separately requested operation may use the reconciled evidence, but no action, payment or subscription is created or authorized by this draft. |
| legal eligibility / fund administration specialist | Exact criterion, required documents, contradictory record, dated amount and source locators. Human interpretation resolves contractual definitions and legal eligibility. |

For every inbound unresolved concern, create one `upstream_issues` item with the originating
artifact ID, code, literal message, status unresolved and material source IDs. Register those source
IDs locally with their original provenance. A resolved item requires attributed dated resolution
and its citations; do not silently drop the original record or mark it resolved from a ready label.
If an artifact uses `unresolved_issues`, map it explicitly; supplying that top-level alias rejects.

For outbound recipients accepting the same schema, pass existing upstream items and map each new
finding to `{artifact_id: this output.artifact_id, code, message, status: unresolved, source_ids}`.
Resolve each finding’s path to the retained record(s) for exact citations; include contributing
notice, movement, position, policy and account records for numerical findings. Missing evidence
is itself unresolved; never fabricate source IDs to make a handoff pass. Preserve household,
request/as-of, capacity/jurisdiction, input hash, result values and source registry.

For recommendation review, map each material concern into the appropriate evidence record’s
`unresolved_issues` with code/message/source_ids and origin upstream-artifact, plus the originating
skill, artifact_id and input_hash required by that schema. A documented assessment cannot erase it.
No hash, version, named reviewer or artifact status authenticates authority or source truth.
