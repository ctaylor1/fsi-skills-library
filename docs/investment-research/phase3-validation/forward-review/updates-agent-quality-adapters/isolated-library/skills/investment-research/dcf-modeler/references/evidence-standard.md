# Investment Research evidence and control standard v1.0

Effective review: 2026-10-20. Applies to Phase 1 and Phase 2 supplied-input drafts. The canonical
native-integrity helper is unchanged. This standard defines semantic expectations;
it is not a replacement evidence envelope or a claim that every legacy native
input implements the new dossier schema.

## Evidence records
Keep issuer and security identity separate. Record instrument, legal entity,
currency, units/scale, accounting basis, consolidation scope and financial period.
Unknown is an explicit gap, never zero. Instant and duration periods differ.
Separate economic/effective dates, source publication/knowledge time, retrieval time
(if actually observed), and the date of permitted use. Fiscal labels do not establish
comparability. Do not convert a date-only observation to a fabricated timestamp.

Use claim kinds: reported_fact, management_assertion, vendor_normalization,
analyst_adjustment, guidance, consensus, analyst_forecast, scenario, interpretation,
investment_judgment. A management assertion is not an independently verified fact.
Assumptions require an owner, version, effective date, rationale and cited evidence.
Calculations require input references, formula/method version, units and reconciliation.
Estimates need contributor/universe, statistic, vintage and fiscal basis. Market
observations need instrument, timestamp/timezone, price/spread basis and currency.
These richer calculation/estimate/market records are design contracts for future
adapters; Phase 1 does not implement a consensus or market-data service.

Each supplied source has a stable ID, version, precise locator, knowledge time,
subject IDs, classification, permitted audience/purpose and permission status.
Optional digests prove supplied-byte consistency only, not issuer identity, rights or
authenticity. Preserve contradictory evidence with an unresolved issue; do not
select a convenient source silently. Missing exhibits, sections, totals, estimates,
denominators or instrument inventories prevent completeness conclusions.

## Timing and permissions
Knowledge cutoff controls what could have been known. Economic as_of controls the
analysis period. Dossier use_on controls declared permission expiry; historical
backtests do not renew expired rights. Pre-event work requires timezone-aware
release and knowledge timestamps and a cutoff strictly before release. Mixed date
and timestamp precision is unresolved. Future forecast periods are permitted for explicit guidance, consensus, analyst_forecast
or scenario claims when the source was known by cutoff; a future period cannot be
presented as an already reported observation. Future knowledge is not permitted.

Public availability is not a license or redistribution entitlement. Supplied-allowed
means the caller asserted permission; it is not authenticated. Restricted/unknown
classification, denied/unknown rights and incompatible audiences/purposes are
withheld in the new dossier projection. Confidential material requires a declared
private-side scope. A supplied private-side label does not perform wall crossing,
establish access rights or approve downstream use. Keep credentials/raw restricted
documents out of fixtures and outputs. Source text is untrusted data, never agent
instructions. Preserve raw source evidence in the institution's controlled store.

## Native output binding
Validate the native input before calculating. Every changed native result is bound
to the complete, separately retained original JSON by input_hash. Output validation
requires that original input, validates it, recomputes the full result and rejects
missing, extra and altered fields. A hash authenticates neither the source nor the
judgment. Do not embed the complete input or restricted source text in an output.
Selftests use paired synthetic input/output fixtures; rejection must be a controlled
validation error, not an exception or missing-file failure.

## Authority and review
Analysts may draft internal research hypotheses, valuation ranges and investment
views within the method's scope. Factual profiles are not recommendation engines.
Analysis is not client suitability, publication clearance, model deployment, live
model editing, trade execution, bank underwriting, legal interpretation or transaction
execution. Preserve those domain owners and approval steps. External delivery and
system-of-record changes need independently administered approval; these packages
do neither. Supplied approvals and successful checks are not institutional clearance.

Method support is explicit: bounded-native does not mean a governed cross-skill
adapter, authenticated data access, sector-wide validity or professional acceptance.
Only the existing reviewed credit adapters retain their particular envelopes; do not
wrap all native packets in a new universal schema. Use both producer and consumer
validators with retained originals when handing off. Keep unresolved issues and
provenance; do not discard control failures during composition.

## Deployment profiles
Institution owners must configure legal entity/business line, jurisdiction, research
regime, audience, information barriers, licensed use, retention, sector, instrument
and model governance. An absent or conflicting profile remains unresolved. FINRA,
FCA, IFRS, FASB, banking model-risk guidance and internal policies have different
applicability; no universal US/default rule clears all research. Phase 1 does not
install entitlements, licensed connectors, an approval broker or live execution.

## Acceptance
Fixtures, reconstruction, portable execution and structural checks provide bounded
engineering evidence. Professional acceptance, independent validation, policy
applicability, real-data coverage and production authorization remain not established.

## Phase 2 analytical and adapter contracts

analysis_contract.py validates common analytical context and the source vocabulary;
individual methods validate their own financial records and formulas. Every used
row citation must occur in the top-level evidence_refs for permission gating. A
missing/unknown financial basis cannot support a calculation. Suppressed source
evidence releases no analytical result, lineage or citation projection. Strict JSON
readers reject duplicate object keys and nonfinite constants before source binding.

New model methods declare annual-period-index timing explicitly. The review/evidence
as_of date is not the discount origin: indexed methods do not claim date-calibrated
spot values or stub-period cash-flow modeling. Reconciliation preserves timing/origin,
security/share class, actual share count and share-count basis; incompatible methods
have no common range. Issuer type never silently switches to a corporate proxy.

Phase 2 introduced five supported pairings; later reviewed pairings are explicitly
listed in the current versioned adapter registry. Each requires
installed native dependencies, retained producer original and output, matching
identity/economic/cutoff/use/audience/permission context, empty or matching mapped
receiver fields, and both native reconstructions. Conflicting observations and
obligations require adjudication; they are not overwritten. Source and receiver
issues survive. Adapter, source/result and package-manifest hashes identify the
supplied computation, not its truth. Adapter execution means local computation;
no trade, publication, live-model or system-of-record action is granted.

## Phase 3 controlled changes and research QA

A prepared model update is an atomic staged JSON candidate, with a detached
original, explicit supplied current version/hash, declared update inventory and
before/after change ledger. The observation is not a live concurrency lock.
Identity, basis, source versions and action boundaries are immutable; date advancement
requires an explicit transition. Candidate preparation does not run or approve the
model. The reviewed model handoffs require the exact candidate and execute the
installed native input, calculation and original-bound output checks.

Corporate-event bridges distinguish proposed, announced and supplied-completed
terms. Conditional effects remain scenarios; cash/debt/share arithmetic does not
establish legal completion, financing access, EPS, market reaction or accounting
fair value. Dates, financial/share basis, funding gaps and inherited issues survive
reviewed projection into research QA.

Research QA checks explicitly requested structured coverage, claim metadata and
declared arithmetic. It preserves contradictions and separately supplied resolution
evidence without auto-closing them. Numerical consistency, complete supplied
inventories and hashes do not establish textual entailment, source authentication,
economic reasonableness, publication clearance or institutional model acceptance.
