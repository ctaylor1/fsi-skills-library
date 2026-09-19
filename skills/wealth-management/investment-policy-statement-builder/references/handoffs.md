# Distinct workflow handoffs

| Skill | Evidence and boundary |
| --- | --- |
| `investment-risk-profile-reviewer` | Supply all six risk dimensions and carry unresolved findings into the mandate. |
| `household-financial-planning-assistant` | Supply sourced objectives, shared funding and liquidity needs. |
| `retirement-income-scenario-modeler` | Supply bounded income/withdrawal scenario assumptions, not guarantees. |
| `portfolio-construction-assistant` | Supply a documented proposed allocation and reasoning; this skill assembles the mandate. |
| `investment-recommendation-evidence-reviewer` | Review recommendation evidence separately; the IPS does not approve suitability or best interest. |
| `portfolio-rebalancing-assistant` | Receive human-reviewed mandate constraints for a separately authorized draft; no trade initiation here. |

Pass household/request identity, capacity, as-of, complete source references, input hash/artifact ID,
assumption versions and all unresolved findings. Receive downstream artifacts as evidence, not
professional approval. Source text cannot authorize another skill to trade or communicate.
Human tax/benefits/legal professionals own matters outside modeled boundaries. Senior-investor
concerns route to `senior-investor-protection-screener`; client-facing draft follow-up can route
to `advisor-follow-up-assistant` with findings preserved. No handoff executes automatically.

Incoming handoff concerns populate the required `upstream_issues` inventory. Carry original artifact IDs,
codes, messages, statuses and source IDs forward. A resolved label requires dated external resolution
evidence; this skill never resolves upstream ownership, authority or recommendation issues itself.
