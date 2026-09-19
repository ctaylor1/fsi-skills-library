# Source Map — payment-integration-readiness-reviewer

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Integration attestation/config record (system of record) | Item attestations, evidence refs | Read-only |
| 2 | Approved readiness-checklist config (versioned) | Required items, categories, gate items | Read-only |
| 3 | Reference data | Category normalization | Read-only |

The attestation record is the system of record; the pack never marks an item attested or changes
config.

## Citation format
`{system}:{ref}@{version}` — e.g. `attest:integration=INT-77;item=idempotency@2026-07-18`,
`checklist:go_live@v2026.05`. Every gap cites its item and the checklist version.

## Freshness / effective dates
- Checklist config is a **versioned contract**; the output records the version used.

## Least-privilege operations (deployment)
- `attest.read(integration_id)` → item attestations — read-only, bounded.
- `config.get('go_live_checklist', version)` → required items + gate flags — read-only.
Durable `packet_id`; below the fixed timeout; no mutation.

## Phase 1 implementation boundary

Phase 1: readiness is based on supplied review declarations. A nonempty evidence_ref is not inspected evidence. N/A needs a separate applicability review; manual reconciliation is an alternative control, not an exemption. No offline score authenticates reviewers, proves test results or approves go-live.

Declared inspection schema: evidence_review.status=inspected, reviewer, reviewed_at (offset-aware ISO timestamp), scope, result_ref. Each declaration is supplied evidence; it is not authenticated by this tool.

## Phase 3 source basis (reviewed 2026-09-18)

Native inputs are supplied operational evidence: queue snapshots, authoritative payment
outcomes, trace/release/status records, financial reconciliations, scoped test artifacts,
cost ledgers and task/model evaluation results. Prefer original versioned artifacts over
summary decks. Register source dates and review_due; preserve contradictory observations.
Offline scripts inspect supplied contents but do not authenticate identity or fetch links.

Engineering references, not payments law or certification requirements:
- [Amazon Builders Library, idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/): preserve client request identity and changed-intent boundaries.
- [Google SRE Workbook, postmortem culture](https://sre.google/workbook/postmortem-culture/): retain incident evidence, learning and accountable follow-up.

The formulas, baseline fault scenarios and AI evidence fields are library design
conventions. Reassess source versions before applying to a deployment; contractual,
scheme, security and jurisdiction requirements need their current authoritative pack.
