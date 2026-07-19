# Domain Rules — model-inventory-maintainer

Deterministic rules for maintaining model/agent inventory records. Thresholds and maps are
**configuration** (versioned, owned by Model Risk Governance), not hard-coded judgments, and
never tuned to an individual owner. Orientation references: SR 11-7 (model risk management),
the firm's model-inventory standard, and the AI/agent governance policy take precedence.

## Required inventory attributes

An inventory record is **complete** when every required attribute is present and evidenced:

| Attribute | Meaning |
| --------- | ------- |
| `name` | Human-readable model/agent name |
| `owner` | Accountable owner (role and, where an individual, masked identity) |
| `purpose` | Business purpose / intended use |
| `lifecycle_status` | Current lifecycle state (see state machine below) |
| `materiality_factors` | The four scored factors (see rubric) |
| `versions` | Version list with effective dates |
| `dependencies` | Upstream models/services/data the asset depends on |
| `lineage` | Datasets/features feeding the asset (from the data catalog) |
| `approvals` | Prior governance approvals on record (if any) |

A missing required attribute is a **completeness finding**; the skill records it and never
fabricates a value.

## Materiality rubric (deterministic, versioned)

Four factors, each scored **0–3** with documented anchors:

| Factor | 0 | 1 | 2 | 3 |
| ------ | - | - | - | - |
| `financial_exposure` | none | low | moderate | high |
| `decision_autonomy` | advisory-only | human-in-the-loop | human-on-the-loop | autonomous |
| `customer_impact` | none | internal only | customer-facing (indirect) | direct / adverse-action |
| `regulatory_use` | none | supporting | regulatory-report input | regulatory decision (capital / credit / AML) |

`score = financial_exposure + decision_autonomy + customer_impact + regulatory_use` (0–12).

| Materiality tier | Rule (default config `inv-rubric-2026.07`) |
| ---------------- | ------------------------------------------ |
| **Tier 1** (material) | `score >= 8`, **OR** any escalating factor (`decision_autonomy` or `regulatory_use`) `>= 3` |
| **Tier 2** (moderate) | `score` in 4–7 and no escalation |
| **Tier 3** (low) | `score <= 3` and no escalation |

The computed tier is authoritative. If the `proposed_record.materiality_tier` differs from
the computed tier, that is a **materiality-mismatch finding** (severity high) for the
adjudicator — it is never silently overwritten and the owner never negotiates the tier.

The **effective** rubric thresholds used for the tie-out (defaults merged with any
deployment/jurisdiction `config` override) are echoed into `materiality_tie_out.config` so
the output validator re-derives the tier with the *same* configuration the compute step
used, not the hardcoded default. A non-default rubric (e.g. a stricter jurisdiction pack)
therefore ties out to itself; when no config is echoed the validator falls back to the strict
defaults.

## Lifecycle state machine (allowed transitions)

| From | Allowed next |
| ---- | ------------ |
| `proposed` | `in-development`, `retired` |
| `in-development` | `in-validation`, `on-hold`, `retired` |
| `in-validation` | `approved`, `in-development`, `on-hold`, `retired` |
| `approved` | `in-use`, `in-validation`, `retired` |
| `in-use` | `in-validation`, `on-hold`, `retired` |
| `on-hold` | `in-development`, `in-validation`, `in-use`, `retired` |
| `retired` | (terminal — no transitions) |

For `create`, the proposed status should be `proposed` or `in-development`; a create that
declares `approved`/`in-use` without approvals evidence is flagged. For `update`, a
`current_record.lifecycle_status` → `proposed_record.lifecycle_status` transition not in the
table is an **invalid-transition finding**; the skill flags it and never normalizes it.

## Source reconciliation & break taxonomy

Comparable attributes (default: `name`, `owner`, `lifecycle_status`, `latest_version`) are
reconciled between the proposed record and the authoritative source snapshot (registry, then
catalog for lineage). Each comparison yields one result:

| Result | Break type | Meaning |
| ------ | ---------- | ------- |
| `match` | — | Proposed value equals the source value |
| `break` | `value_mismatch` | Both present but differ |
| `break` | `missing_in_inventory` | Present in source, absent from the proposed record |
| `break` | `missing_in_source` | Present in proposed record, absent from the source snapshot |
| `break` | `stale` | Source snapshot older than the staleness window (default 90 days) |

Every break is **typed** and carries the citations to both sides. Breaks are findings for
the adjudicator; the skill never resolves them by overwriting a value.

## Hard boundaries (fail closed)

- Never approve, attest, certify, or clear a model/agent; never post/register the record.
- Never close a finding or file anything — the proposal `requires_adjudication`.
- Never tune materiality to the owner or business pressure; use only the versioned rubric.
- Never silently resolve a reconciliation break or normalize an invalid lifecycle transition.
