# P0, P1, P2 and P3 route map

| Intent | Target | Required evidence |
| --- | --- | --- |
| book-review | `advisor-book-of-business-reviewer` | Explicit book scope, per-household service records, policy priorities, owner capacity and economic measures |
| prospect-referral | `wealth-prospect-referral-preparer` | Permitted prospect/referral sources, attributed facts, service-fit questions, contact permissions and suppression evidence |
| discovery | `wealth-client-discovery-assistant` | Household facts, goals and cited unknowns |
| household-reconciliation | `household-wealth-data-reconciler` | Confirmed account scope, snapshots and explicit ownership shares |
| onboarding | `wealth-onboarding-packager` | Account registration and current firm onboarding profile |
| risk-profile | `investment-risk-profile-reviewer` | Cited willingness, capacity, horizon, liquidity and constraint evidence |
| financial-plan | `household-financial-planning-assistant` | Reconciled household balance sheet, cash flow, debts, goals and supplied scenario assumptions |
| investment-policy | `investment-policy-statement-builder` | Household objectives, six distinct risk dimensions, constraints and a human-owned investment mandate |
| retirement-plan | `retirement-income-scenario-modeler` | Account balances/treatments, spending, dated income streams and scenario assumptions |
| portfolio-construction | `portfolio-construction-assistant` | Approved supplied models, investable assets, target allocation, restrictions and concentration constraints |
| proposal-comparison | `portfolio-proposal-comparator` | Comparable proposal positions, underlying exposures, costs, liquidity and client constraints |
| rebalancing | `portfolio-rebalancing-assistant` | Position and tax-lot inventory, targets, price/fee/settlement evidence and transition constraints |
| tax-review | `tax-aware-investment-reviewer` | Cited tax lots, household/spouse/IRA activity, supplied equivalence, rates and asset-location policy |
| estate-review | `estate-wealth-transfer-reviewer` | Sourced estate intentions, account title, beneficiary designations and governing-document inventory |
| family-governance | `family-wealth-governance-preparer` | Family decision process, succession and next-generation discussion preparation |
| trust-administration | `trust-administration-reviewer` | Trust-capacity engagement, governing obligations, beneficiary/distribution evidence and accounting review |
| protection-needs | `protection-needs-reviewer` | Sourced survivor, disability, long-term-care or liability scenario and existing coverage |
| performance-report | `wealth-performance-report-builder` | Valuations at cash-flow boundaries, fees, approved benchmark and official reconciliation reference |
| account-service | `wealth-account-service-packager` | Requested service, account/authority records, balances, positions and firm service conditions |
| fee-review | `advisory-fee-reviewer` | Effective agreement, household billing group, valuation segments, exclusions, charges and conflict review |
| manager-due-diligence | `investment-manager-due-diligence-reviewer` | Investor mandate, manager evidence, cited diligence policy, fees/liquidity and monitoring requirements |
| lending-liquidity | `wealth-lending-liquidity-reviewer` | Household funding need, protected cash, supplied liquidation analysis, current loan terms, encumbrances and rate/collateral stresses |
| private-markets | `private-market-client-reviewer` | Client commitments, dated notices and settlements, valuation/eligibility evidence, manager diligence and account-specific liquidity budgets |
| recommendation-evidence | `investment-recommendation-evidence-reviewer` | Proposed recommendation and controlled capacity/applicability profile |
| client-review | `client-review-preparer` | Cited household review records and current template/applicability configuration |
| follow-up | `advisor-follow-up-assistant` | Sourced meeting record, decisions, recipients and current communication configuration |
| investor-protection | `senior-investor-protection-screener` | Dated observations, transactions and firm screening configuration |

`goal-progress` is an alias for `financial-plan`; map it to target mode `goal_progress` when preparing the household planning input. Map `financial-plan` to target mode `household_plan`; when both were requested, use household_plan with the specified goals and preserve the explicit goal-progress request in context. Specifying both creates one target step with both modes recorded. Investor protection is prioritized when explicitly requested. Remaining steps follow the displayed lifecycle order; no unrequested prerequisites are automatically run. Manager due diligence is an investor-side Asset Management workflow.

Map natural-language requests to these explicit intents; the script does not interpret free text. Distinguish protection-needs planning from possible investor exploitation, portfolio construction from comparison and rebalancing, and service packaging from performing a transfer. P3 family-governance and trust-administration are distinct from estate planning and account service; supplied discussion agreements never replace governing authority.

The legacy financial-goal-progress-analyzer package is replaced by `household-financial-planning-assistant`, retaining goal-progress mode. The legacy suitability-reg-bi-reviewer package was replaced in P0 by `investment-recommendation-evidence-reviewer`. Neither legacy name is a second installed skill or runtime redirect. Update installed manifests and caller schemas to the new names before removing legacy installations.

For `book-review`, supply `scope_type: advisor-book`, `book_id`, and `household_id: book:<book_id>` in the routing context. The collection marker exists only to reuse the versioned evidence envelope; it is not an actual household identity. Missing/inconsistent book scope remains a needs-data routing plan. Combining a book scope with client/prospect targets requires separate subject requests and retains a finding. Every step declares target_scope. Prospect/referral work needs its target case scope and contact evidence; router readiness cannot supply those facts.

Subject scope: family-governance requires scope_type `family-group`, family_id and household_id `family:<family_id>`; trust-administration requires scope_type `trust`, trust_id and household_id `trust:<trust_id>`. Advisor-book retains its existing book marker. Mismatched or missing subject fields create findings. Any reserved marker used for another target creates a separate-subject finding, even when scope_type is absent. Actual household/beneficiary associations need explicit reviewed mapping and fresh target validation.

An explicit prospect-case scope also creates a separate-subject finding for any non-prospect target. Prepare an evidenced association to the actual subject before proceeding. Legacy requests without scope_type retain earlier routing behavior; that absence never authenticates identity.
