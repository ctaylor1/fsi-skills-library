# Asset Management Phase 4 implementation

Authorized October 4, 2026. Phase 4 adds six specialist packages and six explicit extensions, bringing Asset Management to **64 implemented packages**, including its router. These cover the bounded methods in the [support matrix](SUPPORT-MATRIX.md); they do not establish complete professional coverage or production acceptance. The branch remains `feature/financial-services-expansion`; no commit, push, merge, release or live operation was performed.

## New packages

| Capability | Implemented method and boundary |
|---|---|
| [C08 portfolio-transition-planner](../../skills/asset-management/portfolio-transition-planner/SKILL.md) | Human-supplied cash-equity/ETF trade slices; aggregate daily participation, available shares, conservative settlement cash, costs and target reconciliation. No optimizer or execution. |
| [K07 securities-financing-reviewer](../../skills/asset-management/securities-financing-reviewer/SKILL.md) | Securities lending and repo perspectives; distinct haircut/initial-margin conventions, source-position collateral allocation, declared constant-basis simple accrual, recalls and funding. No enforceability, netting or margin instruction. |
| [S06 private-fund-financing-reviewer](../../skills/asset-management/private-fund-financing-reviewer/SKILL.md) | Subscription/NAV facility credit bases, lender concentration convention, exact covenants and simple financing costs. No facility approval or covenant legal opinion. |
| [S08 private-fund-restructuring-reviewer](../../skills/asset-management/private-fund-restructuring-reviewer/SKILL.md) | LP secondary proceeds and GP continuation elections, allocation of fees/carry, rolled capital, new commitments, conflicts and supplied consents. No fairness opinion or transaction recommendation. |
| [S09 tokenized-fund-operations-reviewer](../../skills/asset-management/tokenized-fund-operations-reviewer/SKILL.md) | Legal-register/token native-unit/wallet/custody and omnibus reconciliation; finality and transfer restrictions from supplied evidence. This optional capability serves a distinct operational job; no token transfer or register certification. |
| [G05 sustainability-mandate-reviewer](../../skills/asset-management/sustainability-mandate-reviewer/SKILL.md) | Long-only weighted metrics, denominator reconciliation, coverage, vintage, estimated data and exclusions under effective supplied mandate terms. No sustainability rating or legal compliance certification. |

## Explicit extensions

| Existing owner | Selector | Added scope |
|---|---|---|
| [portfolio-hedge-reviewer](../../skills/asset-management/portfolio-hedge-reviewer/SKILL.md) | `advanced-derivatives` | Bound full-book/scenario PV and Greeks from a versioned supplied engine and independent benchmark; cost-adjusted scenario differences. No local nonlinear pricer. |
| [portfolio-performance-attributor](../../skills/asset-management/portfolio-performance-attributor/SKILL.md) | `specialist-attribution` | Multiplicative local/FX interaction, parallel duration/convexity approximation, supplied factor contributions, chronological recursive linking, retained residuals and engine-result challenge. |
| [systematic-investment-research-reviewer](../../skills/asset-management/systematic-investment-research-reviewer/SKILL.md) | `walk-forward` | Frozen protocol/selection, sample configuration pins, label/feature chronology, embargo, historical universe and net cost paths. No backtest simulation, PBO or significance claim. |
| [etf-operations-reviewer](../../skills/asset-management/etf-operations-reviewer/SKILL.md) | `specialized-basket` | Multicurrency bond clean/accrued values, one-to-one custom substitutions, reviewed calendars and supplied-engine derivative values. No basket publication or settlement. |
| [institutional-investment-solutions-planner](../../skills/asset-management/institutional-investment-solutions-planner/SKILL.md) | `liability-real-assets` | Dated liability cashflows and supplied discount-factor scenarios, duration/convexity arithmetic, real-asset commitments and liquidity stress. No actuarial certification. |
| [investment-regulatory-obligation-reviewer](../../skills/asset-management/investment-regulatory-obligation-reviewer/SKILL.md) | `jurisdiction-profile-comparison` | Reviewed entity/activity/product/investor/territory profiles, primary-source bindings, lifecycle, deadlines and overlaps. No universal rules or independent legal applicability determination. |

Earlier schemas remain available when `extension` is omitted; unknown extensions fail. Each package includes instructions, schema/method references, practitioner templates, source controls, fixtures, negative cases and detached-original output validation. Primary references are methodological background; institution-reviewed source records still determine actual applicability.

## Reuse, packaging and routing

Neutral issuer/security research remains owned by Investment Research. No research package was duplicated into AM. Existing shared professional owners and canonical foundation methods remain intact.

The canonical [specialist contract](../../shared/asset-management/specialist_contract.py) is generated and version/hash pinned into the twelve packages. It rejects JSON floats before specialist calculations, preserving exact decimal strings/integers. Its [engine evidence contract](../../shared/asset-management/specialist-engine-contract.md) requires full outcome-relevant input, context, pinned engine/method/model versions, exact metric coverage/units and separately supplied benchmark evidence. Missing, partial, unsupported or failed results, mismatched inputs and benchmark misses withhold dependent values. The library neither invokes those engines nor authenticates their approval or benchmark independence.

The router has **59 declared intents** and preserves explicit receiving modes/extensions. Derivatives implementation now routes to the hedge reviewer; staged transitions have their own route. The common evidence registry contains 67 canonical entries, 62 supporting at least one native schema; earlier blocked schemas remain blocked. A declared route does not launch a workflow or prove installation.

Catalog JSON/CSV, approved additions/overrides, resource locks, package manifests, capability matrix and preservation evidence are updated. See [contract and packaging guidance](CONTRACTS-AND-PACKAGING.md) and [Phase 4 validation](phase4-validation/README.md).

## Verification and remaining acceptance

The repaired isolated run passes **701 executable command checks across 93 packages**. Independent forward reviews cover all twelve authored methods and retain eight initial defects separately from repaired evidence: four attribution/research cases, three private-fund cases and one sustainability case. Financial arithmetic, temporal/scope failures, engine result substitution and detached-input validation are tested; counts overlap and are not additive. Final checks also pass264 AM repository tests,910 full repository tests,2,245 whole-library executable checks, and370-package structure with zero errors/warnings. The validation record distinguishes these overlapping scopes and concurrent catalog metadata changes.

Live engine integration, actual licensed sources, institutional profiles, external workbook reconciliation, professional/model/legal review, real-model agent behavior and production acceptance remain open. Synthetic records, hashes and deterministic checks establish bounded implementation behavior, not those external facts or approvals.
