# Insurance implementation plan

Authorized on 2026-09-18 by the request to implement the next phase following the
comprehensive insurance review. This record turns that review into bounded releases.
It does not authorize transactions, customer communications, filings, or payments.

## Phase 1 — correctness, contracts, and routing

The initial state has 24 insurance packages. No earlier insurance implementation
record exists. Existing wealth-management and payments changes are independent work
and must be preserved. The phase creates one router and merges two overlapping
pairs, producing 23 insurance packages; it does not create the later-phase portfolio.

Required outcomes:

1. Correct paid-versus-reported reserve terminology, quote comparability, renewal
   periods/earned premium, claim missingness/timing, treaty scope/arithmetic, and CAT
   feed-health/clearing semantics. Strengthen supporting evidence and validators.
2. Merge the model runner into P&C reserving and FNOL/readiness into claim intake,
   preserving useful stage outputs and documenting input migration.
3. Align all existing package names and descriptions with the actual jobs. Keep
   policy explanation, prospective coverage gaps, claims QA, and health appeals
   distinct; do not claim that later coverage/valuation/life workflows exist.
4. Provide a shared evidence/data contract with explicit actor, object, sources,
   dates, financial basis, unresolved issues, and independent result states.
   Bundle dependencies for independent installation; hashes are not authentication.
5. Route to installed capabilities, require capacity/line clarification where it
   changes ownership, and expose later-phase gaps instead of wrong substitutions.
6. Validate native receiver input at handoff; a common envelope never proves
   compatibility. Preserve unresolved issues and access boundaries.
7. Persist rename/merge decisions through catalog overrides and update active
   references. Record limitations and acceptance evidence separately.

Exit checks: package and catalog consistency; no dangling/circular insurance
handoffs; meaningful regression cases for the identified defects; shared-resource
drift checks; actual native-input handoff tests; bounded independent behavioral
evaluation. Software checks do not establish actuarial/legal professional acceptance
or deployment readiness. Planned natural-language cases are not executed tests.

## Subsequent phases

2. End-to-end operating foundations: product design, rate adequacy, policy
   transactions/billing, producer/placement/delegated authority, claims coverage,
   handling, financial evaluation/payment review, life underwriting/service/death
   benefits, reinsurance program and administration.
3. Analytical and specialist depth: strategy/economics/portfolio performance,
   experience studies, life pricing/valuation/ALM, premium audit/compensation,
   recoveries/disability, fraud analytics/SIU, assumed reinsurance, exposure/CAT,
   finance/capital/ORSA/market conduct.
4. Architecture and measured automation: insurance workflow/data/core modernization
   plus shared solution architecture, automation assessment, data-product value
   evaluation, and operations performance. Integrate approved sources and evaluate
   actual benefits and failure paths before expanding execution.
5. Conditional specialist/regional extensions: parametric trigger review, full
   health-payer pricing/utilization/payment/network jobs, additional market and
   jurisdiction profiles. Require a recurring job, specialist owner and evidence.

## Architecture decisions carried forward

- Keep installable packages flat; use the router/index for capability discovery.
- Use line, market, participant/capacity, and jurisdiction profiles rather than
  duplicate whole workflows by product or vendor.
- Preserve professional ownership of actuarial, claims, product/distribution,
  reinsurance, finance and technology methods.
- Reuse existing data/AI, financial-crime, compliance, security, risk, service,
  finance and enterprise capabilities with explicit input adapters.
- Start with reviewed source profiles; a US orientation is not proof of state
  applicability. Full health-payer scope and execution remain separate decisions.
- Admit a new skill only for a distinct recurring trigger, accountable user,
  evidence contract and useful professional output.

Implementation evidence and remaining acceptance boundaries are maintained in
[Phase 1](PHASE1-IMPLEMENTATION.md), [Phase 2](PHASE2-IMPLEMENTATION.md),
[Phase 3](PHASE3-IMPLEMENTATION.md), [Phase 4](PHASE4-IMPLEMENTATION.md) and
[Phase 5](PHASE5-IMPLEMENTATION.md).
Phase 2 added 17 operating foundations; Phase 3 added 21 specialist workflows.
Phase 4 added three Insurance design packages and four shared review/measurement
packages on 2026-09-20, bringing Insurance to 64 and the library to 303 packages.
Implementation and bounded validation of Phases 1–4 are complete. On 2026-10-04,
the user authorized the next phase. Phase 5 installs the five explicit parametric
and health-payer review jobs, bringing Insurance to 69 packages. Its source profiles
require actual market/program/product/jurisdiction evidence rather than regional
defaults. The bounded authoring scope is complete; comprehensive health-payer scope,
additional regional methods, actual source, qualified practitioner and deployment
acceptance remain separate. See the [Phase 5 evidence](phase5-validation/README.md).


## Phase 6 — offline acceptance evidence preparation

After the completed Phase 5 checkpoint, the user requested the next phase. The
follow-on is scoped to local readiness tooling using the existing nine release
gates: exact package/evaluation snapshots, isolated portable checks and supplied
institution-specific review records. No new skill packages are required. Missing
scope and approvals remain missing; evidence inventories never authorize release.
See [implementation](PHASE6-IMPLEMENTATION.md), [review guide](acceptance/README.md)
and [validation](phase6-validation/README.md). Actual institution/source/practitioner
and deployment acceptance, the external source workbook and further domain/market
expansion remain outside this tooling completion claim.
