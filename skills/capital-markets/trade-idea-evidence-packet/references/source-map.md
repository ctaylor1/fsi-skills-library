# Source Map — trade-idea-evidence-packet

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Market data / research | Supporting data points, values | Read-only |
| 2 | Suitability config (versioned) | Restricted products, general-only rules | Read-only |
| 3 | Reference data | Instrument normalization | Read-only |

Market data and research are the evidence; the packet cites every data point and never
distributes or recommends to a client.

## Citation format
`{system}:{ref}` — e.g. `data:point=DP-2;source=vendor_feed@2026-07-18`. Every data point and
every gap/flag cites its source.

## Freshness / effective dates
- Data points are cited to their source and as-of; the packet does not restate market values.
- Suitability config is a **versioned contract**; the output records the version used.

## Least-privilege operations (deployment)
- `data.read(idea_id)` → supporting points — read-only, bounded.
- `config.get('suitability', version)` → restricted/general-only rules — read-only.
Durable `packet_id`; below the fixed timeout; no mutation; no client distribution.
