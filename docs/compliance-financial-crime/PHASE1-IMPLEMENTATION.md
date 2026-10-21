# Compliance & Financial Crime Phase 1 — 2026-09-21

The user authorized Phase 1 after the architecture review. This implementation repairs
and scopes every original package, adds the domain router and common evidence controls,
and records the later professional workflows as planned. It does not implement Phases 2–4.

There are **15 packages in Compliance & Financial Crime**, including the new router,
plus the moved privacy package in Data, AI & Model Governance. The repository catalog
contains **332 packages across 15 categories** at this integration checkpoint. The
36-workflow target is a capability roadmap, not a count of completed professional jobs.

## Delivered behavior

| Original workflow | Phase 1 implementation and limit |
| --- | --- |
| Regulatory change | Source lifecycle, publication/effective/compliance dates, explicit applicability and implementation unknowns; elapsed effective dates do not prove overdue compliance; fixtures are clearly synthetic. |
| Policy/procedure gaps | Unsupported comparisons and evidence expectations remain gaps; future readiness is retained; document presence cannot establish operating effectiveness. |
| Customer due diligence | Renamed customer-due-diligence-reviewer; supplied policy profile and explicit coverage govern bounded review; missing identity, ownership or screening evidence cannot become a clean track. Full lifecycle CDD remains planned. |
| Beneficial ownership | Renamed beneficial-ownership-analyzer; proportional corporate equity method, exact threshold arithmetic, root control and individual document support; trust/complex legal tests remain unsupported. |
| Customer risk rating | Explicit weights/methodology, missing/stale factor propagation, withheld scores and bands, documented unverified overrides; no prohibited-customer determination. |
| EDD | Renamed enhanced-due-diligence-assessor; claim/source assembly and unknowns; residual risk remains Unknown and readiness means assembly for human review. Full substantive EDD assessment is Phase 2. |
| Adverse media | Source-side identity, event/publication chronology, scoped negative searches and linked dispositions; unresolved allegations remain unresolved; PEP and sanctions routes are distinct. |
| Sanctions match | Renamed sanctions-match-investigator; direct OFAC aggregation, evidence dates and SSI distinction; foreign/indirect legal tests remain unsupported; no restriction or clearance authority. |
| AML triage | Missing evidence remains unrated; exact duplicate proposals require scoped dated authorization evidence; invalid chronology blocks favorable suppression treatment. No queue mutation. |
| SAR draft | Material narrative/rationale tied to exact supplied facts, future activity surfaced, draft authorization bound to source; blocked material withheld; no suspicion decision or filing. Full investigation route is explicitly planned with human FIU fallback. |
| Conflicts | Unknown values, policy, MNPI and aggregation remain unknown; approvals checked for scope/time; mere document presence earns no mitigation credit. |
| Employee trading | Renamed employee-trading-preclearance-reviewer; account, policy, timestamped screening and supplied calendar bind a review plan; no execution steps or authenticated approval token. |
| Exam response | Exact assertion/evidence coverage, dates and individually assessed approval records; conflicting authorization remains visible; no submission or closure. |
| Transaction monitoring | Renamed transaction-monitoring-scenario-evaluator; shared five-rule replay utility, explicit PASS/WARN/BREACH/NOT_EVALUABLE, rolling windows and evidence-bound deduplication. Aggregate flow ratio has no transaction linkage. It is not full case investigation. |
| Privacy | Moved to Data, AI & Model Governance; controller/privacy ownership and DPO advice; claim-level evidence, legal-context gaps, inherent indicator separated from unassessed residual risk; no automatic Article 36 conclusion. |

All native calculators validate inputs. All output validators require a detached original
and exact reconstruction, reject unsupported added narrative or raw original embedding,
and retain `source_truth=unverified`. This is evidence integrity, not source authentication.

## Routing, shared components and migration

The router covers the 27 reviewed request types using explicit declared intent and scope.
It distinguishes planned methods, missing context, unknown installation, uninstalled
packages and action requests. It returns a review plan; it does not install or launch skills.
The capital-markets surveillance route explicitly offers bounded case support and leaves
broader scenario design partial. Financial-promotion separation remains planned.

The common contract extends workflow-evidence/1.0 and uses the existing native integrity
helper. It preserves context, source versions, issues, classifications and separate action
states. Actual producer output and receiver input validators run. Every receiver field
requires a reviewed exact mapping to detached source values or supplied supplemental
input. Changed scope/time/audience, lost source records and forged outputs fail. Eleven
native schemas have explicit identity/time adapters; four remain native-only. There is
no implicit triage-to-investigation-to-SAR conversion or external disclosure projection.

Canonical policy validation, scenario replay, native execution, evidence and source
resources are pinned by version, SHA256 and MIT license in the compliance resource lock.
Generated copies and package manifests support isolated installation; no runtime sibling
package import is required. Use `tools/sync_cfc_resources.py --check` to detect drift.

All 15 original dispositions are recorded. Six legacy names and the former privacy path
resolve through `tools/resolve_skill.py` without duplicate active packages or authority.
Active adjacent-domain references were updated. Approved overrides and the provisional
router survive catalog regeneration. The catalog was rebuilt with `--from-current`;
the external source workbook was not edited or reconciled.

## Evidence and remaining acceptance

See [validation record](phase1-validation/README.md),
[independent forward review](phase1-validation/forward-review.md),
[support matrix](SUPPORT-MATRIX.md) and [implementation plan](IMPLEMENTATION-PLAN.md).
The independent forward review preserves seven initial failures and their subsequent
repairs, rather than treating self-consistent golden fixtures as domain truth.

No live institutional connector, authenticated approval service, source certification,
professional/legal acceptance, jurisdiction-complete rule pack or production deployment
has been established. No customer status, queue, filing, account, policy or system was
changed. No commit, push, merge or release was performed. Other-domain work already in
progress was retained; the integration updates its active references, not its methods.
