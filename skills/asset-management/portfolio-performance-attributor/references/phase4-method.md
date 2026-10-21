# Specialist attribution contract

Select `extension: specialist-attribution`. Provide `method_source_ref`, observed `period_start` and `period_end`, `return_unit: decimal`, `basis: gross-of-fees|net-of-fees` and a nonnegative reviewed `tolerance`.

## Supported methods and inputs

- `method: currency`: `segments` must contain unique `id`, `source_ref`, exact matching period dates, complete beginning `portfolio_weight` and `benchmark_weight` inventories each summing to1, `local_currency`, `fx_convention: base-per-local`, `portfolio_local_return`, `benchmark_local_return`, `fx_return`. Local returns and FX returns are simple decimal returns. Currencies are uppercase three-letter codes, the base currency must be real, and a base-currency segment must have zero FX return. Provide separate `hedge_source_ref`, `portfolio_hedge_contribution` and `benchmark_hedge_contribution` in base-currency portfolio-return units. Returns combine as `(1 + local) * (1 + FX) - 1`. Active local, FX and interaction effects are respectively `wp*lp-wb*lb`, `(wp-wb)*fx`, and `wp*lp*fx-wb*lb*fx`. Supplied hedge contribution is additive; its source must be known through period end and no overlay is priced.
- `method: fixed-income`: same complete beginning-weight/period rows; each has base `currency`, `yield_unit: decimal`, `curve_method: parallel-duration-convexity`, `yield_change`, `spread_change`, and portfolio/benchmark prefixed `duration`, `spread_duration`, `convexity`, `carry`, `rolldown`, `realized_return`. Contribution per side is carry + rolldown - duration*yield_change - spread_duration*spread_change + convexity*yield_change²/2. Duration is per unit absolute yield, convexity per squared yield; carry and rolldown are nonoverlapping return contributions. This is an approximation with supplied sensitivities, not key-rate/full repricing or option-adjusted attribution.
- `method: factor`: pinned `risk_model_id`, `risk_model_version`, `returns_source_ref`, supplied portfolio/benchmark returns and `factors[{id,source_ref,active_exposure,factor_return,exposure_unit:return-per-factor-return,return_unit:decimal}]`. Effect=active exposure*factor return. No exposure or factor model is estimated.
- `method: linking`: ordered contiguous `periods[{id,source_ref,period_start,period_end,portfolio_return,benchmark_return,effects:{effect_id:decimal}}]` covering the review endpoints. Same effect inventory each period, including explicit zeros. Each period reconciles to its active return within tolerance. Recursively `E[t]=E[t-1]*(1+Rb[t])+e[t]*portfolio_growth[t-1]`. This declared chronological convention exactly reconciles compound active return when inputs reconcile; it is not a claim of a unique linking convention.
- `method: engine`: [specialist engine contract](specialist-engine-contract.md). Purpose must be `specialist-attribution`; request input `attribution_context` exactly matches period_start, period_end, basis and return_unit. Full instruments, model inputs and expected metric inventory belong inside the bound engine request. The tool challenges supplied results only and never launches a pricing/risk model.

Every method retains unexplained residuals. Residual above tolerance is a review issue, not an allocation to another effect. Weights are long-only and beginning-of-period; intraperiod flows, leverage, changing weights and corporate actions require another validated method.

## Reproducible examples

`evals/files/phase4-currency-input.json` decomposes .03194 active return into .023 local, .007 FX, .00094 interaction and .001 hedge. Fixed-income example retains .0045 residual. Factor example retains .001 residual. Linking example yields .0312 compound active return with .0257 selection and .0055 allocation. `scripts/test_phase4.py` contains independent arithmetic and adverse coverage/date/unit tests; generated outputs alone are not independent benchmarks.

## Primary method references

- [CFA currency management introduction](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/currency-management-introduction): local asset and currency return relationship; no CFA certification implied.
- [CFA 2026 CIPM topic outline](https://www.cfainstitute.org/sites/default/files/docs/programs/cipm/2026_cipm_l2_topicoutline_online.pdf): distinguishes duration and full repricing attribution approaches. This package implements only the stated approximation.
- [CFA multicurrency attribution research](https://rpc.cfainstitute.org/research/financial-analysts-journal/1994/multicurrency-performance-attribution): context for separating currency effects. No claim to implement that paper's complete framework.

References reviewed 2026-10-04 as methodological background. They do not establish GIPS compliance or institution-specific acceptance.

## Common envelope and execution boundary

All examples are synthetic and do not establish source truth. Use the common foundation header: `request_id`, `object_id`, `as_of`, `knowledge_cutoff`, `currency`, `audience`, explicit `sources[{source_ref,version,as_of,known_at,locator}]`, and `unresolved_issues`. Dates are ISO calendar dates. Financial numbers are exact decimal strings or integers, never implicit percentages. All referenced evidence must be registered and known by the cutoff. Run the existing input, calculation and detached-input output validators; without an extension the original schema remains available. Unknown extensions fail.

A successful check yields a draft with no execution or external delivery. Retain every unresolved issue. Hashes bind supplied content; they cannot authenticate data, licenses, approval, legal applicability or independent professional acceptance.
