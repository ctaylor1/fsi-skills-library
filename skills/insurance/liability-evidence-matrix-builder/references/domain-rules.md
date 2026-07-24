# Domain Rules — liability-evidence-matrix-builder

Orientation: a factual map of which evidence supports or contradicts each alleged fact, with gaps
made explicit. Mapping only — never a liability finding.

## Matrix construction (deterministic)
For each fact:
| Field | Definition |
| ----- | ---------- |
| `supporting` | Evidence items whose `supports` list contains the fact_id |
| `contradicting` | Evidence items whose `contradicts` list contains the fact_id |
| `status` | `supported` (≥1 support, 0 contradict) · `contested` (≥1 support and ≥1 contradict) · `unsupported` (0 support) |

## Gaps (deterministic)
- `unsupported_fact` — a fact with no supporting evidence.
- `dangling_evidence` — an evidence reference to a fact_id that does not exist.

## Disposition mapping (review-only)
- `matrix-complete` — every fact has ≥1 supporting item and there are no dangling references.
- `gaps-for-review` — ≥1 unsupported fact or dangling reference. A triage suggestion for the
  adjuster, **not** a liability finding.

## Hard boundaries (fail closed)
- Never determine liability/fault/negligence; never apportion responsibility; never resolve
  contested evidence; never infer support for a bare fact.
