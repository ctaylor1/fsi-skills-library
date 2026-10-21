# Domain rules and current authority

Identity factors exclude list severity and transaction-country proximity. An ownership nexus is a separate zero-weight factor and escalation basis, not proof of identity. No user-configured threshold changes the statutory OFAC rule. SSI membership alone is not asset freezing. False-positive recommendations are unavailable when list/source/regime evidence is incomplete. Duplicate linkage requires the same supplied evidence snapshot and an open case; changed facts must be reviewed.

## Sources checked 2026-09-21

[OFAC FAQ 5, updated September 9, 2026](https://ofac.treasury.gov/faqs/5) separates identity investigation, authorizations/exemptions, block versus reject, and reporting/records. [FAQ 10](https://ofac.treasury.gov/faqs/10) distinguishes SSI restrictions from blocking. [FAQ 398](https://ofac.treasury.gov/faqs/398) and [FAQ 401](https://ofac.treasury.gov/faqs/401) address aggregate ownership and indirect chains.

[Current OFSI guidance](https://www.gov.uk/government/publications/financial-sanctions-general-guidance/uk-financial-sanctions-general-guidance) uses more than 50 percent ownership or control and generally does not simply aggregate separate designated persons absent joint arrangements/control rights. [Commission FAQ, May 6, 2026](https://finance.ec.europa.eu/document/download/c7265161-3d9c-42e2-a928-e5b38c02bb92_en?filename=faqs-sanctions-russia-assets-freezes_en.pdf) addresses Regulation 269/2014 ownership/control and aggregation. These are authoritative interpretations of specific underlying regimes; foreign regimes and indirect ownership are not implemented by this Phase 1 calculator.

Guidance is distinguished from binding underlying law; illustrative implementation choices are not legal safe harbors. Phase 1 does not certify professional adequacy.


## Independent forward-test correction

A retrieved snapshot is insufficient without a real list_effective_date on/before the case as_of. Missing, invalid or future list effectivity is an explicit needs-data gap; it cannot support a current match or ownership recommendation. Source truth and regime adjudication remain human responsibilities.

Direct ownership percentages are aggregated with decimal arithmetic before the 50% blocked-interest and 100% total-ownership comparisons. No rounding is used to cross either threshold; numeric conversion is for display only. This bounded calculation still requires authorized review of the ownership evidence and applicable regime.
