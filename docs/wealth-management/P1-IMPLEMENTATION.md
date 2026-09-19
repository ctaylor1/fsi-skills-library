# Wealth management P1 implementation

> Historical P1 milestone. P2 is now implemented; see [current scope](P2-IMPLEMENTATION.md) and [current validation](P2-VALIDATION.md). Counts and later-priority status below describe the original P1 milestone.

Date: 2026-09-16. P1 implements all thirteen agreed practitioner workflows: eight new packages and five substantially revised packages, plus an expanded router. The catalog contains **233 packages across 14 categories**, including **21 wealth-management packages** and the shared manager-diligence package in Asset Management. No workflow was dropped to reduce the skill count.

## Delivered scope

| Priority | Workflow and package | Delivered behavior and method limits |
| --- | --- | --- |
| P1.1 | [Household financial planning](../../skills/wealth-management/household-financial-planning-assistant/SKILL.md) | Renamed and expanded from financial-goal-progress-analyzer. Reconciles monthly cash flow, debt commitments and competing goals against unique funding pools. Retains goal-progress mode and continues inflation through date extensions. Scenario illustrations do not automatically reallocate resources. |
| P1.2 | [Investment policy statement](../../skills/wealth-management/investment-policy-statement-builder/SKILL.md) | Produces substantive sourced mandate sections, allocation/constraint checks, governance and revision lineage. Retains six separate risk dimensions; no invented risk rating or professional approval. |
| P1.3 | [Retirement income scenarios](../../skills/wealth-management/retirement-income-scenario-modeler/SKILL.md) | Models explicit account/income/withdrawal assumptions with annual reconciliations. Separates spending shortfalls from depletion and distinguishes before-horizon from at-horizon outcomes. No inferred benefit eligibility, tax law or stochastic success probability. |
| P1.4 | [Portfolio construction](../../skills/wealth-management/portfolio-construction-assistant/SKILL.md) | Builds constrained candidates from explicitly supplied approved-model records, adapting proportions within model asset classes. Preserves restrictions, position caps, cash and unallocated amounts. No forecast, free-form optimizer or automatic model selection. |
| P1.5 | [Proposal comparison](../../skills/wealth-management/portfolio-proposal-comparator/SKILL.md) | Compares supplied holdings and constituent exposures, costs, liquidity and implementation constraints. Unknown exposure/cost remains unknown; no tax proxy or inferred investment objective. |
| P1.6 | [Rebalancing and transitions](../../skills/wealth-management/portfolio-rebalancing-assistant/SKILL.md) | Generates target-delta drafts or validates proposed transitions, including quantities, cash, supplied tax lots, fees, restrictions and settlement timing. Full input binding replaces approval-token assumptions. Retains R4 classification but implements draft planning only. |
| P1.7 | [Tax-aware investment review](../../skills/wealth-management/tax-aware-investment-reviewer/SKILL.md) | Inventories lots, illustrates transition gains/reserves, compares asset-location policy and screens household replacement purchases. Uses supplied rates, tax terms and equivalence groups. No deductible-loss decision, basis change or trade. |
| P1.8 | [Estate and wealth transfer review](../../skills/wealth-management/estate-wealth-transfer-reviewer/SKILL.md) | Compares recorded title, document links and beneficiary designations against explicit intentions. Identifies missing shares, records and contradictions; does not determine document precedence, enforceability, inheritance or tax treatment. |
| P1.9 | [Protection needs review](../../skills/wealth-management/protection-needs-reviewer/SKILL.md) | Calculates separate survivor, disability, long-term-care and liability scenarios against supplied benefits and designated resources. Level, undiscounted amounts; independent events are not summed. No coverage adequacy or product recommendation. |
| P1.10 | [Wealth performance reporting](../../skills/wealth-management/wealth-performance-report-builder/SKILL.md) | Calculates cumulative account/household time-weighted returns at explicit cash-flow boundaries, reconciles official values/returns, and compares matched benchmarks. Supports end-of-subperiod fees; no annualization, attribution or GIPS assertion. |
| P1.11 | [Account service packaging](../../skills/wealth-management/wealth-account-service-packager/SKILL.md) | Prepares transfer, distribution, authority and beneficiary request evidence under supplied service policy. Checks combined cash/position requests and unresolved conditions. No submission, signature authentication or account change. |
| P1.12 | [Advisory fee review](../../skills/wealth-management/advisory-fee-reviewer/SKILL.md) | Recalculates one household billing group's marginal/cliff fees, exclusions, segment valuations, day-count proration, minimum and adjustments. Compares assessed charges and preserves economic conflicts. No account-level allocation certification, charge posting or refund decision. |
| P1.13 | [Investment manager due diligence](../../skills/asset-management/investment-manager-due-diligence-reviewer/SKILL.md) | Investor-side review of investment, operations, fees, liquidity and evidence under explicit criteria; one-period fee illustration, cumulative household liquidity needs and a monitoring plan. No manager appointment, redemption or live monitoring. |

The [router](../../skills/wealth-management/wealth-management-router/SKILL.md) now selects all eight P0 and thirteen P1 jobs. It prioritizes expressly requested investor-protection work, distinguishes insurance needs from exploitation screening, deduplicates goal-progress/financial-plan requests and identifies Asset Management as the manager-review destination. It selects only requested work and runs no downstream skill automatically.

## Data, calculations and handoffs

All thirteen P1 workflows have substantive domain instructions, exact schemas, source/control references, usable output templates, synthetic requests and executable financial/adverse/tampering cases. The scripts produce structured evidence; follow the package workflow to prepare and review the professional artifact. A template's presence alone is not a completed client deliverable.

The canonical [wealth evidence contract](../../shared/wealth-management/wealth_contract.py) is bundled identically in twenty packages. Its retained identifier `wealth-p0-v1` is the envelope version, not a claim that P1 remains unimplemented. Sources require owners, locators, dates and a validity window. Item-level citations and unknowns remain explicit. Domain outputs preserve the full normalized input snapshot and reconstruct calculations, findings and identity during validation.

The [analysis helper](../../shared/wealth-management/wealth_analysis.py) supplies strict decimal, evidence and CLI routines to the fee, tax and performance packages. Other packages retain local domain utilities and their documented numeric contracts. Some accept only JSON numbers; others accept decimal strings. Rounding conventions also differ by method and are explicit. Never pass an output directly to another workflow merely because the envelope matches.

Every handoff must inspect the originating artifact, preserve identity/capacity/period and source evidence, map the actual domain fields, carry unresolved concerns and validate the target independently. The issue fields are:

| Target | Required issue inventory | Mapping |
| --- | --- | --- |
| P1 router request | `unresolved_issues` and `upstream_artifact_ids` | Each issue has code, message and source_ids; retain originating IDs separately. Empty lists require a reviewed scope. Legacy standalone P0 route requests may omit these lists. |
| Planning, IPS, retirement, construction, comparison, rebalancing, estate, protection, account service and manager diligence | `upstream_issues` | Each record identifies artifact_id, code, message, unresolved/resolved status and source_ids. Carry unresolved originating findings as unresolved; resolution requires its own attributed evidence. |
| Tax, fees and performance | `unresolved_issues` | Each record carries code, message and source_ids; retain originating artifact references with the issue or input context. The full snapshot preserves them. |
| Existing P0 workflows | Their documented package-specific schemas | In particular, recommendation evidence uses an unresolved-issues inventory on each evidence record. Map explicitly and preserve all relevant open concerns. |

No issue-list field can prove that an author did not omit a concern. Hashes detect inconsistent edits, not a consistently falsified replacement input/output pair. Neither supplied approval records nor review-ready status authenticate authority or professional acceptance. Institutional source, identity, audit and retention controls remain separate deployment requirements.

## Migration and catalog persistence

- Replace financial-goal-progress-analyzer with household-financial-planning-assistant in installed manifests, saved prompts and caller schemas. Focused mode is `goal_progress`; integrated mode is `household_plan`. There is no duplicate legacy package or runtime redirect.
- The five revised practitioner packages and router are version 0.2.0. New packages are version 0.1.0. Inputs and outputs are materially different; recreate old artifacts from sources under current schemas.
- The former rebalancing execution, approval-token and rollback examples have been replaced by explicit draft contracts. An R4 catalog label does not enable action. Any actual order/transfer integration needs separate authorization design and certification.
- Eight additions are persisted with source `wealth-management-p1-2026-09-16` in [provisional-additions.json](../../catalog/provisional-additions.json). There are sixty provisional additions in total: 47 earlier, five P0, eight P1. [Approved overrides](../../catalog/approved-overrides.json) retain both P0 and P1 renames and revised metadata when importing the external workbook.
- `python tools/build_catalog_from_xlsx.py --from-current` refreshes JSON/CSV from current approved records without the unavailable external workbook. Regeneration is idempotent. The workbook itself has not been updated.
- Canonical contract updates require deliberate rebundling with `python tools/sync_wealth_contract.py`; `--check` verifies the twenty contract copies and three analysis-helper copies. Packages run without importing sibling skills.

## Priorities retained after P1

The previously agreed later priorities remain unchanged; they are not implemented or cataloged by this work.

| Priority | Planned package | Professional job |
| --- | --- | --- |
| P2 | advisor-book-of-business-reviewer | Service coverage, segmentation, retention, capacity and practice economics |
| P2 | wealth-prospect-referral-preparer | Authorized prospect/referral research and service-fit preparation |
| P2 | wealth-lending-liquidity-reviewer | Household borrowing/liquidity sources, collateral and rate stresses |
| P2 | private-market-client-reviewer | Commitments, calls, distributions, client liquidity and eligibility evidence |
| P3 | family-wealth-governance-preparer | Family decision processes, succession and next-generation discussions |
| P3 | trust-administration-reviewer | Governing-document obligations, beneficiary matters, distributions and accounting evidence |

P0 and P1 are implementation priorities, not release certifications. [P1 validation](P1-VALIDATION.md) distinguishes deterministic verification and independent synthetic scenario review from outstanding wealth-professional/compliance acceptance, real-model evaluation and institution-specific deployment work.
