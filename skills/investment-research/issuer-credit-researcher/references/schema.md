# Native schema

The common envelope remains `schema_version=ir-phase2/1.0` with request, purpose,
audience, typed subject, economic `as_of`, `use_on`, knowledge cutoff,
information barrier, source register, top-level citations and unresolved issues.
Every supplied row citation must be nonempty, registered and declared at top level.
The package accepts issuer or security subjects; security subjects require the
target `issuer_id`. Source eligibility remains a separate control: ineligible
sources withhold the entire result projection.

`issuer_profile` is `nonfinancial-corporate`. `financials` carries `currency`,
`unit`, `accounting_basis`, `consolidation_scope`, `period{start,end,
fiscal_calendar_id}`, citations and nullable `ebitda`, `gross_debt`,
`unrestricted_cash`, `interest_expense`, `operating_cash_flow`, `capex` and
`funds_from_operations`. Its reported period must end on or before both `as_of`
and the UTC cutoff calendar date, retaining declared date precision. Forecast and
scenario financials are unsupported. Future contractual maturities are separate.

Each nullable financial amount may be omitted or explicitly null; both mean
unknown and produce a partial result with an issue naming the missing field.
Only calculations depending on that amount are withheld. The exact original
input, including omission versus null, remains bound to the output. Supplied zero
is a known amount, never a missing-value substitute. Zero EBITDA, interest expense
or reconciled gross debt cannot serve as a positive ratio denominator; the
affected ratio is null and the result is partial. Zero cash-flow numerators and
zero capex remain usable, as do supported signed EBITDA, operating cash flow and
FFO values.

The context fields below mean the exact financial currency, unit, accounting
basis, consolidation perimeter and reporting period. For debt stocks, the period
identifies the financial statement whose end-date balance is reconciled; it does
not turn a principal stock into an income-statement flow. No FX translation,
unit conversion, perimeter inference or accounting-basis conversion is supplied.

## Source-bound economic identity

An event ledger, debt inventory or debt bridge uses `source_binding` with
`source_id`, `version`, `known_at`, `locator`, `subject_issuer_id` and
`economic_event_key`. The source ID/version/knowledge-time precision must match
the registered source. `locator` must equal its registered precise block and
must be cited by that ledger row. The registered source block must identify the
target issuer, including when the request subject is a security.

`economic_event_key` is the supplied canonical economic identity within the target
issuer and financial perimeter/period. It must remain stable across corroborating
documents, locators and versions. Document provenance cannot make the same event
additive. Alias detection uses target issuer plus this key, independently of row
ID, source ID, document version or locator. These are explicit supplied assertions;
the package does not authenticate their real-world accuracy or discover undeclared
aliases across invented keys.

## EBITDA adjustments

`ebitda_adjustments[]` retains unique `adjustment_id`, signed `amount`, `rationale`
and citations, and selects `economic_event_id`, `event_version` and
`aggregation_role` (`event-total` or `component`). Component selections also carry
`component_id`. Exact technical ID duplicates reject before arithmetic.

`ebitda_adjustment_events[]` is the evidence ledger. Each row has unique
`ledger_id`, `economic_event_id`, `event_version`, signed `amount`, context,
`source_binding`, citations, `aggregation` and `components[]`. Supported
aggregation modes are `event-total-only` (empty component list) and
`additive-components` (complete, nonoverlapping component inventory). Each component
has unique `component_id`, signed `amount` and citations. Additive component amounts
must sum exactly to the event amount. The ledger's event total, or all its distinct
components, may be selected once; combining total and components is unavailable.
Each selected adjustment's citations must exactly match its selected event-total
or component citations. Distinct events with equal amounts remain legitimate when
their canonical evidence identities differ.

Missing identity, scope, source binding, version, selection or additive evidence;
multiple candidates or aliases; and conflicting amounts leave the reconciliation
unavailable. The result is partial, with adjusted EBITDA and all adjusted ratios
null. Reported EBITDA is retained. No adjustment rows and no event ledger means a
zero adjustment total; unused supplied events are unresolved, never silently omitted.

## Debt inventory and carrying-value reconciliation

`instruments[]` retains unique `instrument_id`, legal `issuer_id`, `estate_id`,
`seniority`, `currency`, nullable `principal`, `guarantor_ids` and citations.
Included principal also needs explicit `unit`, `accounting_basis`,
`consolidation_scope`, `period` and `principal_basis=contractual-principal`,
comparable to the reported financial context.

Each instrument has `debt_inclusion` with `treatment` (`included` or `excluded`),
`reason`, target `subject_issuer_id`, target financial context and citations. Legal
issuer or guarantee relationships do not silently determine accounting scope.
An explicitly excluded structural instrument may be in another currency, basis or
perimeter, but needs a cited target-scope exclusion. Included null or missing
principal is unavailable; it is not zero. An exclusion lacking its reason or target
scope cannot make an inventory complete.

Omitted or null `debt_inclusion` means the inclusion decision is missing and
withholds debt-dependent ratios. An explicitly excluded structural instrument
may have omitted or null principal without making the included debt inventory
incomplete: its principal does not enter the reconciliation.

`debt_reconciliation` carries target context, `source_binding`, citations,
`inventory_coverage=complete-for-supplied-scope`, a nonempty `coverage_description`
and a `bridge[]`. The declaration is source-bound supplied coverage, not independent
confirmation of inventory completeness. Every instrument still needs an explicit
inclusion or exclusion and the included inventory must reconcile numerically.
Omitted or null `debt_reconciliation` means evidence is unavailable and produces
a partial result with the affected ratios withheld and no bridge lineage.

Each bridge row has unique `bridge_id`, canonical `economic_event_id`, signed
`amount`, `bridge_type=principal-to-carrying-value`, `instrument_ids`, `rationale`,
target context, `source_binding` and citations. The bridge covers included
instruments only, and every included instrument must be covered. An explicit cited
zero bridge is required when principal and accounting carrying value coincide;
their equality is not assumed. Distinct bridge economic identities are applied
once. Included principal plus bridge must equal reported gross debt exactly.

Missing or contradictory coverage, source binding, included principal, currency,
unit, basis, scope, period, bridge identity or total produces a partial result with
gross/net leverage and FFO/debt null. Supported EBITDA, interest coverage and free
cash flow remain available. Principal is never automatically equated with carrying
value, and structural instruments are never automatically consolidated.

## Output and reconstruction

`results.evidence_reconciliation` retains both reconciliation statuses, reasons,
evidence ledgers, selected rows, inclusion/exclusion IDs, principal/bridge/reported
totals and instrument evidence. Calculation lineage identifies selected event,
instrument and bridge IDs plus citations. Exact tieouts use rational arithmetic on
the decimal representation of each finite parsed JSON number; no epsilon or caller
tolerance can waive a mismatch. Displayed calculated numbers and ratios use JSON
numbers and therefore retain ordinary finite floating-point display limits.

Optional `risk_observations[]` retains risk ID, category, observation and citations.
Missing new reconciliation metadata is accepted as incomplete evidence and yields
a partial result; it is never inferred from legacy row IDs. Malformed structures,
duplicate technical IDs or invalid citations reject. The separately retained
original is mandatory for output reconstruction; caller review/pass flags grant
no authority. See the paired synthetic fixtures under `evals/files`.
