# Source Map — insurance-rating-worksheet-builder

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Rate manual / rating-factor config (authority, versioned) | Base rates, factors, fees, min premium | Read-only |
| 2 | Risk-characteristic record | Territory, class, exposure basis | Read-only |
| 3 | Reference data | Class/territory normalization | Read-only |

The rate manual is the authority for rates and factors; the worksheet applies it and records the
version. It never changes the manual.

## Citation format
`{system}:{ref}@{version}` — e.g. `manual:factor=territory@v2026.05`. The worksheet records the
manual version and every applied step.

## Freshness / effective dates
- The rate manual is a **versioned contract**; the worksheet records the version used and the
  policy effective date.

## Least-privilege operations (deployment)
- `manual.get(line, version)` → base rates + factors + fees — read-only, bounded.
- `risk.read(policy_id)` → characteristics — read-only.
Durable `worksheet_id`; deterministic; below the fixed timeout; no mutation; no binding/quoting.
