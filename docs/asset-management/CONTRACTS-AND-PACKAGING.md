# Contracts and portable distribution

## Native calculation boundary

Use the package's documented input schema and local deterministic method. Preserve
the exact original JSON separately. Output validation requires that original input
via `--input`; it checks the complete source digest and reconstructs the native result.
Unknown output fields cannot carry unchecked narrative or restricted evidence.
An approved narrative is a separate reviewed artifact. Full-input hashes identify
the supplied snapshot; neither a hash nor a matching result authenticates it.

The existing household manager-diligence method retains its own stronger native
workflow contract. Its default remains household/US/USD scoped. Phase 2 adds an explicit
`institutional` mode with its own source-supported contract; it does not reinterpret legacy inputs. The source schemas and original method IDs of the
25 research/banking category-only moves remain unchanged.

## Shared artifacts and handoffs

The AM router bundles `investment-evidence/1.0` over the existing
`workflow-evidence/1.0` contract. A common request records professional capacity,
represented party, authoritative native object/date, subject type, jurisdictions,
currency, units, book basis, economic as-of, knowledge cutoff, source versions,
declared permitted use and unresolved issues. Its audience is internal review.
Source permissions and reviewer names are supplied assertions, not authentication.

Only explicit native identity/date adapters may produce these envelopes. A native
schema without defensible identity/date binding remains usable locally but cannot
be wrapped until a reviewed adapter or native schema revision is implemented.
See `NATIVE_ADAPTERS` in the canonical
[investment contract](../../shared/asset-management/investment_contract.py) and the
router's [handoff instructions](../../skills/asset-management/asset-management-router/references/handoff-contract.md).

Artifact assembly invokes the actual installed producer output validator with the
original native input. A handoff requires a receiver-native request and reviewed
field mapping bound to both artifacts: each native leaf must be an exact source copy
or separately sourced additional input. Context changes require an explicit mapping.
Handoff build and validation rerun the actual producer output validator using a
separately retained original source request, then the actual installed receiver input
validator must accept the proposed input. Recomputed envelope hashes cannot bypass
that reconstruction. Explicit integrity-only inspection is not handoff acceptance. Native
findings and upstream unresolved issues survive the handoff; acceptance by the
receiver's schema does not resolve them. No conversion is inferred automatically.

Common contracts distinguish complete/partial/unsupported evidence, calculation
success, human review, delivery and action. Envelopes do not replace native schemas,
grant authority, connect to enterprise systems, or prove source truth. Cross-skill
packets retain internal evidence; outward-facing reports require a separately reviewed
projection and distribution approval.

Five package schemas remain native-only: investment thesis monitoring (multiple subjects with
no batch identity), multi-portfolio mandate review (run scope), counterparty exposure
(timezone-free timestamp), source indexing (job identity) and record normalization
(heterogeneous batch identity). The legacy private-deal committee schema also remains
native-only. New public-security, manager and allocation committee modes are registered.
The registry has67 canonical entries:62 can wrap at least one schema. Phase4 adds six new package adapters and six explicit extension adapters; legacy pointers and blocked schemas remain unchanged. These are adapter dispatch counts, not counts of every native calculation submethod. These counts do not imply every producer/receiver pair
has a valid mapping.

Phase 2 foundations use `investment-foundation/1.0`: object_id, as_of, knowledge_cutoff,
currency, internal-review audience, versioned sources, explicit method, draft status
and detached input hash. Each domain requires the observation links in its schema.
The common wrapper must preserve native source versions, dates, permission restrictions,
cutoff and audience. Its units must be `native-schema`: monetary amounts, return fractions
and ratios keep their native field conventions. A wrapper cannot silently relabel them
as millions or percentage points. Missing linked evidence is rejected or withheld with
visible issues according to the domain method.

## Canonical source and package generation

Maintain reusable code in `shared/investment-data`, `shared/asset-management`,
`shared/investment-analytics` and the existing `shared/workflow-review`. The router
also bundles the legacy insurance contract needed by that workflow adapter.
Professional workflow instructions remain with their canonical skill owner.

`catalog/investment-resource-lock.json` pins each shared source's version, SHA-256
and license. Each affected package's `references/package-manifest.json` records its
bundled resources, file digests, local Python runtime and external dependency boundary.
Bundles are generated; never patch them independently. To deliberately release a
reviewed shared-resource update into these package artifacts:

```bash
python tools/sync_investment_resources.py --update-lock
python tools/sync_investment_resources.py --check
python tools/build_asset_management_index.py --check
python tools/check_asset_management.py
```

Use `tools/resolve_skill.py <legacy-name-or-path>` to inspect a migration. A merged
alias returns its required mode; the caller must construct the canonical wrapper
input. The resolver never executes a workflow. The two merged packages retain
separately testable native modules and require explicit mode selection.

Isolation checks copy all 93 migrated or newly added affected packages into a temporary directory and execute
its native evaluations without a repository-wide runtime or sibling skill imports.
Declared institutional engines, licensed data, authentication and human approvals
remain deployment dependencies. Package integrity is distinct from those dependencies.

Phase 3 also generates pinned copies of the actual shared owner `domain.py` methods
under explicit `shared_architecture`, `shared_data_value`, `shared_operations` and
`shared_automation` module names. Their professional instructions remain with the
owners; AM adapters add investment-specific contracts. Shared methods run in their
native decimal context and their outputs are reconstructed from a separate supplied
input, bound to object, date, currency and source versions. The original shared
packages remain unchanged.

Only the data architecture package includes the optional
[read-only gateway client](../../shared/asset-management/licensed_data_connector.py).
Its [contract](../../shared/asset-management/gateway-contract.md) requires an
independently administered policy and credential, TLS, exact request/principal scope,
nonce, fresh affirmative permission and bounded responses/retries. The library does
not provision the gateway or authenticate offline receipts. Synthetic transports
cannot claim a live access observation, and saved receipts never authorize new reads.

## Local methods and approved engines

Transparent local implementations cover bounded checks and independent challenge
calculations. Specialist optimization, full repricing/risk and production accounting
require a separately accepted engine or system of record. The versioned
[engine contract](../../shared/investment-analytics/engine-contract.md) records method,
implementation, input provenance, time, units, assumptions, coverage, residuals and
origin. An unavailable engine produces an explicit gap; it cannot silently select
a simplified method. No vendor integration is implied by this interface contract.

The implemented native artifact adapters accept only `local-analysis`. External-engine
and system-of-record origins are reserved by the engine interface and require their
own accepted adapter. Method ID/version text is labeled `caller-declared-unverified`;
a native reconstruction check does not independently certify that label or method.

## Specialist methods and engine evidence

Phase4 adds explicit `extension` dispatch for advanced derivatives, specialist attribution, walk-forward research, specialized baskets, institutional liability/real-asset scenarios and jurisdiction-profile comparisons. Unknown extensions fail; omitting the extension keeps earlier methods. Foundation wrapper fields, units and source metadata remain bound to native originals.

The canonical [specialist engine contract](../../shared/asset-management/specialist-engine-contract.md) binds a complete outcome-relevant request, exact metric units/inventory, object/currency/as-of/cutoff, engine/method/model versions and independent benchmark evidence. Missing, partial, unsupported, stale, mismatched or out-of-tolerance results cannot produce dependent financial values. The engine is not invoked; institutional approval and benchmark independence are declarations needing separate authentication. No local nonlinear pricing fallback is supplied.

All Phase4 specialist inputs reject JSON floats and require exact decimal strings or integers. `specialist_contract.py` is generated from canonical shared source and pinned across the twelve packages; the three engine-consuming packages also bundle its reference contract. Transparent local calculations retain their documented approximations, ratios, residuals and unsupported cases.
