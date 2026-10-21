# Source hierarchy and verification

Use issuer/agent event notice, custodian eligible-position record and settlement receipt as the domain evidence. Reconcile conflicting snapshots with the data owner; preserve discrepancies and exact version/known-at dates. Registry and source-use assertions are supplied evidence, not live authentication. No retrieval connector is bundled.

## Primary method references

- [DTCC distributions service](https://www.dtcc.com/products-and-services/asset-services/corporate-actions-processing/distributions). US depository operational description, current Q2-2026 statistics on page; not a universal entitlement/legal rule. Supports the distinct announcement, entitlement, allocation and reconciliation workflow.
- [DTCC event taxonomy](https://www.dtcc.com/products/training/helpfiles/asset_services/corp_actions_browser/help/ann_eventype_sub_eventypes.htm). Operational event taxonomy, verified2026-09-21. Cash dividends and stock splits are distinct events; broader listed events are not implemented here.

References checked2026-09-21. They explain method context and jurisdiction/status; they do not replace vehicle-specific documents or establish legal applicability. Recheck changed law/guidance and the deployed method before reliance. Record economic date separately from date known; never use evidence learned after the request knowledge cutoff.
