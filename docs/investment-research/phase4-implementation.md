# Phase 4 implementation — Investment Research

Implemented 2026-10-20: five specialist research methods complete the 42-capability
target portfolio. The library contains 42 installed IR packages and 395 global
packages. This completes the agreed package roadmap within each method's documented
bounds; it does not establish universal market/instrument coverage or professional,
institutional or production acceptance. [Validation evidence](phase4-validation/README.md)
records the actual checks and retained limitations.

| New package | Implemented research scope |
|---|---|
| macroeconomic-researcher | Cutoff-eligible releases and vintages, revisions, comparable within-series transformations, supplied outlooks and explicit research questions/counter-evidence. |
| cross-asset-theme-researcher | Causal hypotheses and counter-evidence, asset coverage and falsifiers, explicit scenarios with supplied linear/duration sensitivities, and preserved macro driver observations. |
| sovereign-credit-researcher | Government/debt/GDP scope, nominal annual debt dynamics, primary-balance and FX conventions, financing gaps, separate external liquidity and qualitative coverage. |
| public-finance-credit-researcher | GO versus dedicated-revenue security, fiscal/fund/pledge scope, direct debt service, cash/coverage stress, separately identified overlapping/contingent exposure and research gaps. |
| structured-credit-researcher | One reviewed simplified sequential-pay period, collateral/default/recovery/prepayment assumptions, tranche loss allocation, fee/interest/principal/reserve priority and explicit trigger/conservation checks. |

## Macroeconomic evidence and thematic transmission

Series records preserve geography, frequency, measure/unit, real/nominal and price
base, seasonal adjustment and annualization conventions. Selection uses the latest
supplied release eligible at the research cutoff for each series/period. A later
revision does not overwrite historical knowledge; future or imprecise releases have
explicit exclusion reasons. Missing latest values remain unavailable rather than
falling back to a more convenient older observation. Calculations identify their
actual observation endpoints and conventions. Annualization is a mathematical
comparison, not a prediction.

The common source gate remains conservative: an ineligible top-level cited source
withholds the whole analytical projection. Row selection does not authenticate an
external real-time database or silently bypass permissions. Macro interpretations,
analyst forecasts, supplied consensus and scenarios are distinct, with assumptions
and counter-evidence retained.

Theme research separates observed driver evidence from hypothetical shocks and
supplied sensitivities. A duration approximation or linear response does not
estimate causality, establish probability, aggregate incompatible asset measures or
recommend portfolio weights/trades. Required asset coverage and observable falsifiers
make missing or contradicted research scope explicit. Source-text synthesis and
economic plausibility remain professional review tasks.

## Specialist credit boundaries

Sovereign research preserves government perimeter, gross debt, nominal GDP, currency,
accounting basis, dated baseline and explicit annual financing assumptions. Fiscal
cash and committed financing are distinct from whole-economy reserve statistics.
An arithmetically generated debt path does not establish market access or a debt
sustainability judgment. Institutional, political, policy and external research
coverage must remain visible alongside the numbers.

Cash and noncash debt-creating adjustments are separate: both affect debt stock,
but a noncash recognition is not automatically a cash financing need. An explicit
fiscal cash draw reduces debt creation and cannot exceed capacity or gross needs;
unused capacity does not count as funding. Public-finance debt-service inputs
carry exact fiscal-period and security identities.

Public-finance research preserves issuer/fund/security and jurisdiction. General
obligation resources and a revenue system's pledged cash flows are different inputs;
net and gross revenue pledges cannot be substituted. Direct obligations, overlapping
shares, contingent claims, pension exposures and capital needs retain their separate
scope. Supplied document definitions do not establish legal enforceability,
tax exemption, covenant compliance or a rating.

A gross pledge's numerical coverage can coexist with an economic operating-cash
deficit. Both the pledge ratio and the separate system operating balance are
reported; a deficit remains an unresolved finding in baseline or stress results.

Structured-credit research supports the explicitly named simplified profile, not
arbitrary CLO, RMBS, ABS or other deal models. Complete identified collateral and
note inventories, governing version and reviewed priority assumptions are required.
The model separates principal, interest, reserves, losses and immediate recoveries;
its trigger timing and distribution order are explicit. Collateral/security documents,
servicing, legal and omitted model features require additional research. No rating,
tranche price, investment recommendation or complex-engine validation is inferred.

Strict trigger comparison uses the exact rational reconstruction of the declared
decimal inputs, with explicit numerator/denominator and a display-only float ratio.
Equality does not breach a strictly-less-than rule; no rounding tolerance changes
the contractual comparison. The supported future period is at most 366 days,
with year fraction supplied rather than an inferred day-count convention.

## Reviewed composition and discovery

The ninth reviewed mapping, macro-observations-to-theme, transfers only an explicit
nonempty observation-ID subset from actual macro output into an empty/equal theme
driver_observations field. Both inputs retain the same economy, research dates,
cutoff, purpose, audience and barrier. Release/vintage, geography, frequency and
basis metadata survive unchanged. Unselected observations have exclusion records.
The receiver's shocks and causal claims are not inferred or overwritten.

As with earlier mappings, the tool checks exact installed package inventories and
manifest digests, validates the actual producer with its retained original, runs the
actual receiver and reconstructs its complete result. Source collisions, conflicting
populated fields, unavailable selected releases and context drift reject. Inherited
issues remain open. Other specialist pairings remain native-only unless separately
reviewed; common terminology is not evidence of interoperability.

The router and support indexes now describe all 42 installed target methods with
actual native subject/profile limits. The canonical evidence standard is 1.2.0
and reviewed-handoff implementation 1.3.0. New packages, current catalogs and pinned
portable resources are synchronized. Existing native engines, fixtures, aliases and
exact legacy auditor mode are preserved. Prior Phase 1–3 implementation/validation
records remain unchanged; existing methods receive only the reviewed standard and
its package pin.

## Verification and remaining acceptance

A pre-edit source-byte baseline captures 19,032 files, including the initially dirty
checkout. Scope auditing attributes this phase through those bytes rather than the
aggregate Git diff. Saved catalog regeneration uses approved additions/overrides and
--from-current; it does not claim reconciliation to the external source workbook.

All five packages use supplied JSON with strict finite/duplicate-key parsing,
source/citation controls and full detached-original reconstruction. Unit/CLI tests
and independent fresh-case reviews exercise actual methods and the macro adapter.
Exact commands, numerical expectations, findings, repairs, package/evidence hashes
and saved-artifact readback are retained in the validation directory.

The agreed package roadmap is authored. Authenticated/licensed data, broader
geographic/security/model coverage, independent practitioner/model/legal/control
acceptance, institutional deployment and live authorization remain separate work.
No source connector, publication, model write, financing or trading authority is
created by this phase.
