# Handoffs

| Distinct job | Route and content |
| --- | --- |
| Resolve household/account economic data | household-wealth-data-reconciler; source snapshots and mismatches |
| Establish mandate, objectives and constraints | investment-policy-statement-builder; sourced client/risk facts |
| Create candidates from approved models | portfolio-construction-assistant; mandate, universe, model versions |
| Compare supplied candidates | portfolio-proposal-comparator; full candidate holdings, costs and exposure sources |
| Plan a selected-target transition | portfolio-rebalancing-assistant; sourced target selection and current positions/cash/lots |
| Assess lot/account tax consequences | tax-aware-investment-reviewer; candidate or transition, lot facts and unresolved tax coverage |
| Review recommendation evidence | investment-recommendation-evidence-reviewer; full artifact and all unresolved issues |

Preserve artifact_id, input_hash, household/capacity/date/currency, original source registry and every
material finding. Downstream schemas differ: explicitly map fields, reconcile source IDs and retain
upstream artifact references; passing one package does not establish another package's completeness.
The recommendation reviewer receives unresolved costs, exposures, liquidity and tax concerns in its
structured unresolved_issues list. Do not erase them because source metadata says documented.
The authorized professional selects investments and decides any delivery or subsequent action.


## Exact upstream issue mapping
- Governance and other portfolio outputs using `result.upstream_issues`: carry each record unchanged,
  then append relevant new unresolved findings with the producing artifact's artifact_id.
- Router handoff context or tax/fee/performance inputs using `unresolved_issues`: map each code,
  message and source_ids to this package's upstream_issues, set status unresolved, and associate it
  with its actual originating artifact_id. If the router lists several artifact IDs, inspect them
  to establish each issue's origin; do not guess or copy the wrong identity.
- Other source-bound artifacts: read the complete findings and source facts, then encode every
  material unresolved concern with originating artifact_id, original code/message and cited sources.
  Preserve known resolved history only when the supplied source review documents its resolution;
  passing local arithmetic or a model approval label does not resolve an upstream concern.

Merge source registries by source identity, reconcile collisions and update item references together.
An omitted origin/citation requires more source evidence. Do not insert empty lists to pass validation.
When sending this artifact to investment-recommendation-evidence-reviewer, map each unresolved concern
into its relevant check's unresolved_issues entry, using origin upstream-artifact and
upstream_artifact {skill, artifact_id, input_hash} from this output, retaining the cited original facts.
The receiving review must retain substantive blockers; no handoff authenticates approval or closure.
