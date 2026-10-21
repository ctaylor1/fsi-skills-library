# Domain and routing rules

## Declared jobs and examples

These are interpretation examples for the calling agent, not a natural-language
classifier implemented by the calculator. Preserve multiple requested jobs as separate
intents and choose the actual common subject only where it is valid for each job.

| Declared intent | Example request | Subject example | Current route |
| --- | --- | --- | --- |
| manager_economics | Explain fee-revenue change from flows, markets and product mix. | manager | bounded_route / asset-manager-economics-analyzer |
| portfolio_underperformance | Explain why this portfolio underperformed its stated benchmark this quarter. | portfolio | bounded_route / portfolio-performance-attributor |
| mandate_review | Check applicable issuer limits and proposed-state mandate exposures. | mandate | bounded_route / investment-mandate-reviewer |
| tax_aware_sma_rebalancing | Plan a tax-aware rebalance for this separately managed account. | account | bounded_route / tax-aware-portfolio-implementation-reviewer |
| fund_liquidity_stress | Assess redemptions against fund asset liquidity and cash needs. | fund | bounded_route / fund-liquidity-assessor |
| trading_cost_review | Review portfolio fills against supplied execution benchmarks. | portfolio | bounded_route / transaction-cost-estimator |
| etf_launch | Evaluate the operating and commercial requirements for launching an ETF. | fund | bounded_route / investment-product-lifecycle-planner |
| index_tracking | Diagnose index-fund tracking and reconstitution. | fund | bounded_route / index-portfolio-reviewer |
| institutional_manager_due_diligence | Review the institutional manager candidate organization, process and track record. | manager_candidate | bounded_route / investment-manager-due-diligence-reviewer / mode `institutional` |
| private_credit_review | Review a private-credit investment covenant, terms and credit risks. | security | bounded_route / private-credit-investment-reviewer |
| private_fund_performance | Calculate LP net performance and facility effects in a private fund. | investor | bounded_route / private-fund-performance-analyzer |
| private_capital_activity_and_pacing | Review fund capital calls, distributions and future commitment pacing. | fund | bounded_route / private-fund-capital-activity-reviewer |
| nav_discrepancy | Investigate NAV control breaks for a fund share class. | share_class | bounded_route / fund-nav-control-reviewer |
| institutional_rfp | Prepare a sourced institutional RFP response using approved answers. | manager | bounded_route / institutional-proposal-responder / mode `rfp` |
| product_lifecycle_economics | Compare closing, merging or continuing an investment product. | fund | bounded_route / investment-product-lifecycle-planner |
| investment_data_platform | Design point-in-time investment data ownership, lineage and book interfaces. | platform | bounded_route / investment-data-architecture-planner |
| investment_platform_modernization | Plan investment-platform replacement and reconciliation cutover. | platform | bounded_route / investment-platform-modernization-planner |
| investment_ai_workflow | Design a controlled AI-assisted investment workflow and evaluations. | platform | bounded_route / investment-ai-workflow-designer |
| investment_regulatory_change | Assess a rule change for fund jurisdiction, activity and effective date. | fund | bounded_route / investment-regulatory-obligation-reviewer |
| asset_owner_solution | Structure an asset-owner mandate, manager oversight and spending framework. | investor | bounded_route / institutional-investment-solutions-planner |
| household_retirement | Plan our household retirement goals and savings. | investor | out_of_domain / household-financial-planning-assistant |
| asset_manager_stock_valuation | Value the listed shares of an asset manager as an investment. | issuer | out_of_domain / coverage-initiation-researcher |
| manager_corporate_acquisition | Model the corporate acquisition of an asset-management company. | manager | out_of_domain / merger-model-builder |
| company_laptop_inventory | Count and track the company laptop inventory. | platform | out_of_domain / None |
| institutional_policy | Prepare an endowment investment policy draft with liquidity and allocation ranges. | institution | bounded_route / institutional-investment-policy-builder |
| asset_allocation | Compare the feasibility of these supplied institutional asset-allocation candidates. | institution | bounded_route / asset-allocation-planner |
| portfolio_construction | Check these supplied security-weight portfolios against risk and liquidity constraints. | portfolio | bounded_route / portfolio-construction-analyzer |
| portfolio_rebalancing | Draft lot-rounded rebalance quantities and reconcile cash after quoted fees. | portfolio | bounded_route / portfolio-rebalancing-planner |
| buy_side_trade_planning | Review proposed buy-side order participation and funding readiness. | portfolio | bounded_route / buy-side-trading-planner |
| portfolio_performance_measurement | Calculate time-weighted and money-weighted returns from supplied valuations and flows. | portfolio | bounded_route / portfolio-performance-measurer |
| fund_accounting_preparation | Prepare balanced fund accounting workpapers and compare supplied class NAV. | fund | bounded_route / fund-accounting-preparer |
| asset_servicing | Reconcile a cash dividend entitlement against the received payment. | portfolio | bounded_route / investment-asset-servicing-reviewer |
| fund_investor_operations | Review subscription dealing readiness and indicative share units. | fund | bounded_route / fund-investor-operations-reviewer |
| fund_provider_oversight | Review fund administrator SLA misses and outstanding assurance gaps. | provider | bounded_route / fund-service-provider-oversight-reviewer |
| etf_operations | Check a supplied ETF creation basket and cash component. | fund | bounded_route / etf-operations-reviewer |
| private_investment_diligence | Review a private investment sources-and-uses model and dilution scenarios. | security | bounded_route / private-investment-due-diligence-reviewer |
| private_investment_monitoring | Review a private investment KPI watchlist and upcoming covenant evidence. | security | bounded_route / private-investment-monitor |
| systematic_research_review | Review a proposed quantitative strategy study for leakage and net-return assumptions. | strategy | bounded_route / systematic-investment-research-reviewer |
| private_fund_waterfall | Review a simple whole-fund LP/GP distribution waterfall. | fund | bounded_route / private-fund-waterfall-reviewer |
| investment_distribution | Compare institutional distribution-channel eligibility and fee economics. | manager | bounded_route / investment-distribution-planner |
| investment_client_service | Prepare an institutional client service review and outstanding action list. | manager | bounded_route / investment-client-service-preparer |
| investment_investor_reporting | Draft an institutional investor report from approved performance and capital data. | fund | bounded_route / investment-investor-report-builder |
| investment_disclosure_review | Check an investment marketing draft against approved claims and disclosures. | manager | bounded_route / investment-disclosure-reviewer |
| public_security_committee | Prepare a public-security investment committee decision packet. | security | bounded_route / investment-committee-memo-builder / mode `public-security` |
| manager_committee | Prepare a committee packet on an institutional manager candidate. | manager_candidate | bounded_route / investment-committee-memo-builder / mode `manager` |
| allocation_committee | Prepare a committee packet comparing institutional allocation candidates. | portfolio | bounded_route / investment-committee-memo-builder / mode `allocation` |
| investment_operating_model | Design the target middle-office operating model, retained provider oversight and transition controls. | manager | bounded_route / investment-operating-model-planner |
| derivatives_implementation | Design specialized derivatives implementation using approved pricing and risk engines. | portfolio | bounded_route / portfolio-hedge-reviewer / extension `advanced-derivatives` |
| portfolio_transition | Review staged cash-equity transition participation, deliveries and settlement cash. | portfolio | bounded_route / portfolio-transition-planner |
| securities_financing | Review securities lending and repo collateral, recalls, funding and supplied accrual bases. | portfolio | bounded_route / securities-financing-reviewer |
| private_fund_financing | Review subscription and NAV facility credit bases, covenants and financing costs. | fund | bounded_route / private-fund-financing-reviewer |
| private_fund_restructuring | Review LP secondary proceeds or GP continuation elections, conflicts and expenses. | fund | bounded_route / private-fund-restructuring-reviewer |
| tokenized_fund_operations | Reconcile legal fund register, token native units and wallet or omnibus custody records. | fund | bounded_route / tokenized-fund-operations-reviewer |
| sustainability_mandate | Review supplied sustainability metrics, coverage and exclusions against a mandate. | mandate | bounded_route / sustainability-mandate-reviewer |
| specialist_attribution | Explain fixed-income, currency or factor contributions and link complete periods. | portfolio | bounded_route / portfolio-performance-attributor / extension `specialist-attribution` |
| walk_forward_research | Review purged walk-forward samples, historical universes, costs and trial inventory. | strategy | bounded_route / systematic-investment-research-reviewer / extension `walk-forward` |
| specialized_etf_basket | Review multicurrency bond and custom ETF basket values and delivery conditions. | fund | bounded_route / etf-operations-reviewer / extension `specialized-basket` |
| institutional_liability_real_assets | Compare dated liability and real-asset cashflow scenarios using supplied discount factors. | institution | bounded_route / institutional-investment-solutions-planner / extension `liability-real-assets` |
| jurisdiction_profile_comparison | Compare reviewed jurisdiction profiles for exact entity, product, investor and activity scope. | manager | bounded_route / investment-regulatory-obligation-reviewer / extension `jurisdiction-profile-comparison` |

An excluded job is not activated as an AM investment workflow. An owner candidate is
still subject to its own installation, input and authority controls. Do not replace a
corporate acquisition with fund merger analysis or a listed-stock valuation with fee
revenue analysis merely because each mentions an asset manager.

| derivatives_implementation | Specialized derivatives implementation methods. | portfolio | planned_capability / portfolio-transition-planner |

## Status and inventory semantics

The calculator deduplicates repeated intents in first-occurrence order. It first marks
the route `out_of_domain`, `planned_capability` or `bounded_route` from the declaration;
an incompatible subject overrides that with `needs_scope_clarification`; an execute
request overrides all of these with `execution_not_supported`. Institutional manager-DD and RFP routes require their explicit `institutional` and `rfp` native modes. Committee routes likewise declare a native mode. A bounded route covers only the documented method, not the full professional job.
The full original input, including duplicate intents, still contributes to the hash.

`available_skills` is optional. Omitted means `unknown`; an empty inventory means
`not_installed`; exact canonical-name membership means `installed`. Status describes
the method's bounded support, while installation is reported on every reference. An
installed planned entry remains planned, and a bounded route may be uninstalled.
Inventory is caller-supplied, not independently verified.

## Method and overlay boundaries

Return measurement, attribution and private-fund cash-flow performance are distinct.
Attribution is single-period arithmetic supplied-return analysis with additive FX;
it is not a complete return engine. Euler covariance contributions use the declared
annualized-volatility measure. Liquidity uses a bounded public-asset ADV proxy, with
dated cash forecasting as a separate method. NAV controls do not calculate NAV/share.
Portfolio exposure uses authoritative supplied NAV and preserves unknown coverage.
Mandate checks use supplied effective scoped rules and identify unsupported methods.

Legal vehicle, domicile, jurisdiction, investor type, reporting basis, book/currency,
point-in-time source knowledge, strategy and instrument coverage must be established
by the downstream workflow. UCITS, US registered funds, separate accounts and private
funds do not share an inferred universal rule pack. No GIPS compliance, legal advice,
valuation approval or professional acceptance follows from a successful route.
