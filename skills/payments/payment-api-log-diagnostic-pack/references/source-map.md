# Source Map — payment-api-log-diagnostic-pack

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
