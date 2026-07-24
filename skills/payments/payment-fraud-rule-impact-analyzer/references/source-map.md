# Source Map — payment-fraud-rule-impact-analyzer

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Labeled transaction sample (evidence) | Rule-field values + fraud/legit labels | Read-only |
| 2 | Fraud-rule definitions (versioned) | Current + proposed rule (field/op/threshold) | Read-only |
| 3 | Reference data | Field normalization | Read-only |

The sample is evidence for an estimate, not a production population; the analyzer never deploys a
rule or touches live decisioning.

## Citation format
`{system}:{ref}` — e.g. `sample:batch=SMP-2026-07;rule=RULE-14`. The estimate records the sample
id and both rule versions.

## Freshness / effective dates
- Rule definitions are **versioned**; the output records current and proposed versions.
- The estimate is scoped to the sample window; it is not a production forecast.

## Least-privilege operations (deployment)
- `sample.read(batch_id)` → labeled txns — read-only, bounded.
- `rules.get(rule_id, version)` → predicate — read-only.
Durable `analysis_id`; deterministic; below the fixed timeout; no mutation; no live decisioning.
