# Specialized basket contract

Select `extension: specialized-basket` for source-linked multicurrency, fixed-income and one-to-one custom substitution controls. Earlier simple basket input remains available without the extension.

## Input and method

Provide `direction: creation|redemption`, `basket_type: standard|custom`, pinned `basket_id`, `basket_version`, `nav_snapshot`, `policy_version`, `ap_id`; registered `basket_source_ref`, `nav_source_ref`, `policy_source_ref`, `ap_source_ref`; positive integral `creation_unit_size`, `creation_units`, positive `nav_per_share`, nonnegative `transaction_fee`, reviewed `value_tolerance`, signed `cash_per_creation_unit`, `ap_agreement_current`, and policy_effective_from/to.

`reference_components[{id,instrument_id,quantity_per_unit,source_ref}]` must map one-to-one to all `components`. Each component requires unique `id`, `reference_id`, actual `instrument_id`, `instrument_type`, nonnegative `quantity_per_unit`, `quantity_unit`, `quote_basis`, three-letter uppercase `currency`, positive `fx_base_per_local`, `fx_convention: base-per-local`, as-of `price_date`, `fx_date`, registered price/fx/source refs, `market_id`, `settlement_date`, `latest_delivery_date`.

- Equity uses shares and currency-per-share price; local value=quantity*price.
- Fixed income uses face and clean-percent-of-par; local value=face*(clean_price_percent+accrued_interest_percent)/100. Negative price/accrual is outside this bounded method.
- Derivative uses contracts and engine-currency-per-contract. Supply the [specialist engine contract](specialist-engine-contract.md), purpose `etf-derivative-valuation`, input `components` exactly equal to the derivative rows, and exact expected metrics `{id: component_id, unit: component_currency/contract}`. Missing or failed engine/benchmark evidence withholds basket totals; no local nonlinear price is substituted.

Base value=local value*FX. Base-currency FX must equal1. Securities plus cash per unit is compared with creation_unit_size*NAV. Total ETF shares=size*units. Indicative AP cash=cash*units+fee for creation, cash*units-fee for redemption, in the declared AP-flow convention. A negative result signals the opposite cash direction; no money is moved.

`market_calendars[{id,source_ref,date,open,calendar_version,time_zone}]` must be reviewed supplied calendars for the as-of date. Closed markets, expired policies, AP eligibility gaps and missed delivery deadlines remain issues; calendars and settlement deadlines are not inferred from a universal rule.

A changed instrument or quantity requires custom basket type and `custom_review_id` referencing `custom_reviews[{id,component_id,reference_id,policy_version,reviewer_role,decision:supplied-approved,reviewed_on,source_ref}]`. The supplied review must bind this deviation and policy; its approval is not authenticated. Missing/orphan reviews or incomplete reference coverage reject. Split/merged substitutions, tax-lot optimization, price discovery and actual settlement are unsupported.

## Example and primary references

Synthetic EUR bond: face1000*(98+1)/100=990EUR; FX1.1 gives1089USD. Equity contributes1000USD; cash11 gives2100USD=NAV21*100shares. Two units plus fee5 require indicative AP cash27. Tests independently exercise prices, FX direction, reference coverage, custom review, market closure and date controls.

[SEC ETF small entity compliance guide](https://www.sec.gov/investment/exchange-traded-funds-small-entity-compliance-guide) and [2019 final rule](https://www.sec.gov/rules/final/2019/33-10695.pdf), reviewed2026-10-04, provide U.S. background on custom basket policies, review and records. They are not universal rules, a current legal determination or evidence that this particular fund/AP qualifies. Use institution-reviewed applicable profiles and source records.

## Common envelope and execution boundary

All examples are synthetic and do not establish source truth. Use the common foundation header: `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience`, explicit `sources[{source_ref,version,as_of,known_at,locator}]`, and `unresolved_issues`. Dates are ISO calendar dates. Financial numbers are exact decimal strings or integers, never implicit percentages. All referenced evidence must be registered and known by the cutoff. Run the existing input, calculation and detached-input output validators; without an extension the original schema remains available. Unknown extensions fail.

A successful check yields a draft with no execution or external delivery. Retain every unresolved issue. Hashes bind supplied content; they cannot authenticate data, licenses, approval, legal applicability or independent professional acceptance.
