# Source Map — payment-service-incident-investigator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Payment-gateway / API logs (evidence) | Error entries, endpoints, status, request ids | Read-only |
| 2 | Error-taxonomy config (versioned) | code→category map, next-check mapping | Read-only |
| 3 | Reference data | Endpoint/version normalization | Read-only |

Logs are evidence, not a system of record to mutate; the diagnostic never changes gateway
configuration.

## Citation format
`{system}:{ref}` — e.g. `logs:integration=INT-77;request_id=req_9f2`. Aggregates cite the set of
classified entries; the taxonomy version is recorded.

## Freshness / effective dates
- Taxonomy config is a **versioned contract**; the output records the version used.
- Analyze the supplied log window; state coverage (from/to) rather than assuming completeness.

## Least-privilege operations (deployment)
- `logs.read(integration_id, window)` → entries — read-only, bounded.
- `config.get('error_taxonomy', version)` → maps — read-only.
Durable `diagnostic_id`; below the fixed timeout; no mutation. **PAN redaction runs before any
aggregation or output.**

## Phase 1 implementation boundary

Phase 1 boundary: the calculator categorizes supplied log entries; no success denominator, retry-chain/lifecycle reconstruction or causal incident analysis is implemented. Counts are not an authorization failure rate and most-common error is not proven root cause. A service-incident investigator is later-phase work.

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
