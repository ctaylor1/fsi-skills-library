# Phase 1 implementation — Investment Research

Implemented 2026-10-20: structural cleanup, supplied-evidence standards and control
boundaries. This is bounded library implementation, not professional acceptance or
authorization for live use. [Validation evidence](phase1-validation/README.md)
records the checks and their limits.

## Structure and discovery

The 42-entry target registry contains 18 bounded native target methods and 24 planned
methods. IR has 19 installed packages because the legacy model-roll-forward-auditor
remains installed until the Phase 2 reviewer demonstrates parity. No planned method
is represented by an empty installed package or a catalog availability claim.

Two new packages are implemented: investment-research-router and
research-evidence-dossier-builder. capital-structure-maturity-mapper is renamed to
issuer-capital-structure-mapper. The generic financial-document-version-comparator
is moved and renamed to Data, AI & Model Governance / document-version-comparator.
financials-normalizer stays with Finance & Operations. Historic AM aliases resolve
to terminal targets; current banker handoff names are updated. No duplicate alias
packages are created. Catalog regeneration preserves approved additions and overrides
and rejects duplicate input names.

The current library contains 372 cataloged/installed packages in 15 categories.
The generated [support matrix](support-matrix.md) separates installed scope, future
scope and ownership. The router selects explicit declared intents and supplied
deployment inventory; it neither interprets arbitrary requests algorithmically nor
launches methods. A missing profile, unsupported bank method, planned capability,
unknown installation, absent installation and prohibited action are distinct states.
Dependencies are proposed jobs, not proven composability. Standalone DCF lists its
forecast builder as optional context because no new forecast adapter is implemented.

## Evidence and boundaries

The [canonical evidence standard](../../shared/investment-research/evidence-standard.md)
and [record vocabulary](../../shared/investment-research/research-records.schema.json)
define issuer/security identity, financial periods, source and claim types, knowledge
timing, permitted use, assumptions, market/estimate context and calculation lineage.
The richer market/estimate/assumption/lineage contracts guide future adapters; they
are not new authenticated data services or a universal evidence envelope.

The new dossier projects one issuer/security's supplied claims. It distinguishes
reported facts, management assertions, adjustments, guidance, consensus, forecasts,
scenarios, interpretation and judgment. It checks supplied source identity/version,
precise locations, cutoff precision, future knowledge, declared purpose/audience,
classification and permission expiry against use_on rather than the historical
economic date. Future reported periods are withheld; explicit forecast/scenario
periods can remain eligible. Unknown financial bases, including padded unknown
strings, do not become known values. Withheld claim text is not projected.
Resolution citations survive when permitted; contradictions remain contested until
human adjudication. Completeness refers only to the supplied coverage inventory.

All 21 affected native packages (19 IR and two shared owners) use the canonical
detached native-integrity helper. Calculation validates input before use. Output
validation requires the retained original input, validates it, reconstructs the
complete result and rejects altered, missing, extra or embedded-source fields.
Passing reconstruction proves supplied-input consistency, not truth or rights.

Internal analytical drafting does not grant publication clearance, client suitability,
legal conclusions, credit approval, trade execution, live-model changes or deployment.
Institutional profiles and independent approvals remain with their responsible owners.
The existing narrowly reviewed credit wrappers retain their own contracts; Phase 1
does not claim that every native output can be consumed through those wrappers.

## Native repairs

| Area | Implemented correction / remaining bound |
|---|---|
| Company profiles | Withhold stale, future, mismatched, missing and restricted facts; reject financial booleans/nonfinite values. |
| Initiation | Retain supplied claims; allow signed margins and supported unblended methods without a forced midpoint. |
| Landscape and sizing | Support qualitative scope, eligibility and explicit quantity/price/currency/annual dimensions; incomplete or single-method coverage remains partial. |
| Filing and generic comparison | Reject duplicate IDs; missing section/exhibit/value inventories do not prove removal or complete extraction. |
| Financial normalization | Reconstruct each statement and period; distinguish reported from adjusted identities. |
| Models and valuation | Separate EV multiples from P/E equity-per-share values; require explicit bridge components; label standalone DCF and funding infeasibility. |
| KPI and scenarios | Preserve missing totals, mapping effectivity and complete context binding; no claimed integrated rerunner. Duplicate axes fail. Unbracketed root searches do not prove no interior crossing. |
| Debt and terms | Preserve instrument/legal issuer/document/version/currency and unknowns. Negated seniority is reviewed; percentage floating spreads normalize to bps. |
| Surveillance | FCCR remains a proxy, not DSCR; restricted cash, conditional facilities and incomplete maturities do not establish liquidity sufficiency. |
| Earnings | Pre-event timestamps and fiscal comparison matter; results require cited supplied baselines, without a new production consensus engine. |
| Publication preparation | Unknown applicability/configuration remains unresolved; preparation does not authenticate clearance or distribute research. |

Updated native methods are version 0.2.0; the new router/dossier are 0.1.0. Required
identity, dimension and explicit bridge fields are documented in each package's
schema/native contract and changelog. Old artifacts are not relabeled as new-version
results. The original inputs must remain independently retained under appropriate
institution controls.

## Packaging and verification

Shared resources are pinned in investment-resource-lock.json and bundled into
portable packages by sync_investment_resources.py. Manifest hashes exclude caches
and establish package-byte integrity only. A read-only check detects drift; updating
the reviewed lock is an explicit operation. IR indexes are generated from the
capability registry. Structural checks reject empty inventories and missing positive
or negative executable evidence. The portable runner copies all 21 packages outside
the repository and runs their entrypoints with the selected Python interpreter,
without PYTHONPATH or repository-relative dependencies. Tracebacks cannot count as
successful negative validation.

The checkout already contained substantial unrelated work. A pre-edit source hash
baseline covers 17,681 files. The preservation audit checks every baseline source
outside the explicit implementation scope rather than attributing the dirty Git
diff to this task. This phase adds no commit, push, deployment or external action.

## Remaining work

Phase 2 expands the analytical methods and establishes model-reviewer parity and
reviewed adapters. Phase 3 adds controlled updates, event analysis and research QA;
Phase 4 adds specialist macro/cross-asset/sovereign/public-finance/structured methods.
Sector/instrument coverage, jurisdiction and institutional applicability, licensed
data, entitlements, independent practitioner validation and deployment acceptance
remain explicit gates. No financial-institution valuation fallback is introduced.

Catalog regeneration was checked with the saved current catalog plus approved local
additions/overrides. The external authoritative workbook was not supplied or reloaded;
workbook reconciliation remains unverified. Local idempotence is a narrower claim.
