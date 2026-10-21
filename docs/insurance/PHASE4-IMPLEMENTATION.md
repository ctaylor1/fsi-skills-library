# Insurance Phase 4 — architecture and measured automation

Authorized by the user's 2026-09-20 request to complete Phase 4. The implementation
adds **three Insurance packages and four shared packages**, bringing Insurance to
**64 packages** and the complete catalog to **303**. Work remains on
`feature/financial-services-expansion`; no merge, release or portfolio version bump
is part of this milestone.

## Delivered recurring jobs

| Package | Accountable owner and trigger | Native work product and limits |
| --- | --- | --- |
| `insurance-workflow-designer` | Insurance operations/process architect redesigning FNOL, submission, claims, underwriting or producer support | Current/target serial paths, source/tool contracts, owners, bounded attempts and human failure routes; weighted scenario times. No workflow engine or measured improvement claim. |
| `insurance-data-product-designer` | Insurance data architect/steward designing policy/claim/customer context | Grain, semantic/lineage/access/quality definitions, exact namespaced relationships and as-valid/as-known sample resolution. Conflicting assertions remain unresolved; no identity matching or ACORD certification. |
| `insurance-core-modernization-planner` | Core modernization lead comparing options and migration rehearsals | Requirement fit, identical-horizon supplied costs, policy/form/history and coexistence design, dependency waves, snapshot-bound reconciliation and recovery gates. No option selection or cutover. |
| `solution-architecture-planner` | Cross-domain solution architect reviewing a workload design | Components, interfaces, alternatives, access/failure semantics, scoped observed requirement fit and common-period costs. No provider certification or deployment. |
| `workflow-automation-assessor` | Cross-domain automation/operations owner considering a bounded pilot | Paired observations, error labels, control tests, explicit volume scenarios, capacity hours versus realizable cash and simple payback. No causal estimate or autonomous regulated decision recommendation. |
| `data-product-value-evaluator` | Data owner comparing a supplied product/provider | Licensed-purpose evidence, fixed-version paired outcomes, coverage, temporal leakage, confusion counts, outcome costs and separately reviewed projections. No vendor choice or license authentication. |
| `operations-performance-analyzer` | Operations owner measuring a service queue | Observed UTC window, queue conservation and independent controls, completed-cohort duration/cost/SLA, unfinished ages and labor utilization. No causal or staffing action. |

Shared packages live in Enterprise Functions & Technology (architecture/automation),
Data, AI & Model Governance (data value), and Finance & Operations (performance).
Each package has a native schema/method, primary-source orientation, controls,
handoffs, output template, executable examples and regression methods. Skill entry
instructions require a source audit of review/permission/completeness assertions;
listing records never establishes that an inventory is exhaustive.

## Integration and ownership

The Insurance router now resolves the Phase 4 design and shared assessment intents,
including legacy design requests, to installed targets. It distinguishes missing
installation, unsupported action, missing context and conditional capability gaps.
Full health-payer, parametric and additional regional profiles remain Phase 5
candidates under the agreed roadmap, not implied completed capabilities.

A portable `workflow-evidence/1.0` contract and namespaced review runtime are bundled
from `shared/workflow-review`. Existing Insurance contracts and native runtimes are
unchanged. New receivers explicitly accept validated legacy insurance artifacts;
legacy receivers need reviewed field adapters and retained companion packets.
Scope changes require an exact source-bound context mapping before dependent
calculation. Unclassified unresolved input/upstream issues withhold dependent
measures and recommendations. Unknowns never become zero or a successful outcome.
Native output validators recompute from immutable retained input. Hashes detect
changes, not authenticity or correctness of source mapping.

Integration checks exercise actual receiver CLIs, not just common envelopes:

- Completed operating episodes map into paired baseline measurements, retaining
  separate candidate evidence, units and the explicit nonlabor cost convention.
- Workflow output contracts and accountable owners map into an architecture review.
- Insurance semantic fields map into the existing data-lineage documenter's source
  and output nodes and transformation edges; its native output is validated too.
- A legacy capital artifact supports a source-linked modernization requirement,
  retaining its original evidence format, scope and open issues.

Actual production connector identity, permissions, licensed standards, institution
sources and benefits realization remain acceptance work. These packages integrate
supplied evidence and design source contracts; they do not connect to or operate
insurance systems. Phase 4 does not expand execution authority.

## Verification and findings

See [the validation record](phase4-validation/README.md) for exact commands,
independent raw cases, retained failures, repair replays and file manifests.
The entire library has 1,552 executable package checks, and repository tooling has
377 tests, including 15 Phase 4 integration methods. The seven new packages invoke
130 native method tests inside their 35 package commands; these counts overlap.
All 303 package definitions validate without errors or warnings.

Two independent forward reviews covered all seven jobs and wrote actual draft
practitioner deliverables. They exposed source-to-input over-assertion of review and
completeness flags, interface-guide omissions, and two dependent-result defects.
Original inputs, wrong outputs, explicit mapping corrections and unchanged-input
repair results are retained. Passing command checks do not establish broad model
behavior, actual benefits, qualified practitioner acceptance or production readiness.

## Maintenance and remaining gates

- Keep portable copies aligned with `python tools/sync_workflow_resources.py --check`.
  Existing Insurance contract/foundation checks continue separately.
- Reconcile approved catalog additions with the externally maintained workbook.
- Have named practitioners and data/control owners review actual source records,
  mapping assertions, scope profiles, method limits and practitioner deliverables.
- Before any deployment, establish source/tool access, least privilege, recovery,
  failure ownership, observation protocols, control evidence and measured benefits.
- Request Phase 5 only for an evidenced recurring job, specialist owner and supported
  jurisdiction/product source profile. Existing wealth/payment acceptance work is
  independent and is not closed by this Insurance milestone.

## Concurrent draft preservation

A separate repository review briefly authored the same Phase 4 paths. That task
stopped before consolidation. Its drafts were retained in
`/tmp/fsi-phase4-local-draft-backup` and the full overlapping packages were copied to
`/tmp/insurance-phase4-overlap-preserved`. One seven-package implementation is active;
there is no duplicate automation-assessor package. The other task's cross-domain
acceptance records and all historical validation evidence remain intact.
