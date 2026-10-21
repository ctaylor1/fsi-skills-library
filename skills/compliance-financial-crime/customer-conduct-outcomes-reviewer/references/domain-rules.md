# Bounded practitioner method

Define product/distribution role, observation window, metric and population grain before aggregating. Keep cohort and vulnerable-customer segmentation explicit, including expected but missing groups. Reconcile eligible population, observed denominator and harmful outcomes; a missing or zero denominator yields no rate, while zero observed harms with a valid denominator is an observed zero. Retain missingness, support/value barriers and selection bias. Compare only to supplied review thresholds and avoid extrapolating from a partial sample to all customers.

## Supported scope

The native method reconciles supplied facts using the schema; it does not contain a complete
legal-rule engine. Institutional review criteria must carry exact source-fact references,
version, scope and dates. No legal profile, legal threshold, risk weight, materiality decision
or authority is installed by default. Record unsupported jurisdiction/product/sector profiles
and route contested applicability to Legal. Human narrative must separately distinguish
verified fact, supplied assertion, inference, recommendation and unknown.

## Primary source review (2026-10-03)

- `FCA-PRIN2A9`: [FCA-PRIN2A9](https://handbook.fca.org.uk/handbook/prin2a/prin2as9), source date/version `2026-06-26`. FCA Handbook PRIN 2A.9; live rule/guidance reviewed, conditional on Consumer Duty scope. Supported contextual use: UK FCA retail Consumer Duty only with supplied applicability and distribution role. Review status: retrieved from official source on 2026-10-03; legal/practitioner acceptance not established.

Refresh primary sources and applicable institution policies before each consequential use. The historical SEC staff report is expressly not a safe harbor. DOJ prosecutorial guidance is not universal law. FCA/FINRA/FFIEC sources apply only to their actual perimeter.

## Thematic outcomes review detail

Define the actual product, institution's distribution role and observation window. State the
metric's numerator, denominator, eligible population, observation grain, segmentation basis and
vulnerability identification method before calculating a rate. Never divide harm events by
customer counts if the metric's units differ; reconstruct the supplied metric or withhold it.
The native method checks counts and definitions but cannot independently verify those units.

Expected cohorts are an explicit source-backed list. Missing vulnerable or other expected groups
remain open issues; overlapping all-customer/vulnerable cohorts are shown separately and never
summed. For each group, harm rate = observed harmful outcomes / observed eligible denominator;
coverage = observed denominator / eligible population. Missing or zero denominators yield null,
while a known zero harm numerator with a valid positive denominator yields observed rate zero.
A partial population cannot support a whole-population good-outcomes conclusion.

The human draft triangulates complaint themes, understanding, abandonment, support friction,
fees/benefits and distribution evidence, without conflating isolated complaints with causal
harm. Investigate value/support barriers and cohort differences, source quality and selection
bias. Institution-defined thresholds are review criteria, not a universal conduct score. An
individual complaint and customer-specific remedy stays with its complaint owner.

## Typed count units and supported metric

Supply source-bound `review.population_unit`, `review.numerator_unit` and
`review.denominator_unit` claims. The bounded method supports binary affected-customer
proportions with all three equal to `unique-customers`. Repeated event counts are not
affected customer counts; event/customer, account/customer and other unit combinations
are unsupported and withhold rates and thresholds. Missing units remain a valid
partial intake with unknown metrics; never infer units from prose. Threshold comparison
uses the exact count ratio against the supplied decimal threshold; displayed rounding
does not turn an exception into acceptance.

Decimal `threshold_rate` values must be source-bound decimal strings (for example,
`"0.05"` or `"0.33333333333333333334"`), with the same string in the cited source
fact. The string contains digits with an optional decimal point, is at most 256
characters and lies in [0, 1]. Integer 0/1 thresholds are also exact. JSON fractional
numeric thresholds remain valid partial intake, but their original decimal precision
cannot be established after floating-point parsing; criterion comparison is withheld
and the output requests exact decimal evidence. Displayed rates do not determine
acceptance.
