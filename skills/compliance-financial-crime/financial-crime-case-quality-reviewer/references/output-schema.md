# Native output contract

`compliance-foundation/2.0` returns the exact reconstructed result with input_hash and separate
source/fact bindings; raw original input and raw excerpts are never embedded. All foundation
fields are mandatory including draft=true, human_review_required=true, action_taken=false,
source_truth=unverified, source_assurance=supplied-unverified, approval=not_requested and
execution=not_performed. Validation requires the detached original input and compares all fields.

`results` contains mandate, supported-method state, supplied independence consistency,
legal-profile/authority consistency, population/sample/criteria scope, per-case/criterion checks,
observed criterion counts, case outcomes, coverage, observed case exception proportion and
within_supplied_exception_threshold. The proportion has numerator, denominator, decimal_display,
exact_ratio and population_inference=not-performed. Decimal display uses 28 significant digits;
exact_ratio is authoritative and threshold comparison does not use rounded display.

Each criterion row identifies its native case/criterion/observation, carries its source-bound
observation, eligible pass/fail/unknown state, mechanical exceptions, unknowns and a statement
that substantive human reasoning assurance remains supplied-unverified. Partial rows retain
known exceptions. Coverage explicitly shows unobserved or partial selected case IDs. Retain
all unresolved issues in the foundation envelope and any permitted human narrative.

Fixed professional states: case_closure and sar_filing not-performed; reportability/guilt
not-assessed; assurance_opinion not-issued; legal_privilege not-determined; automated_decision
and reputation_assessment not-performed; narrative_status proposed-supplied-unverified. Changing
any state, result, context, audience, source binding or adding narrative fails reconstruction.

Use assets/output-template.md as a separate human draft; it is never an unvalidated native field.
No external audience projection is implemented. A narrative must be independently checked for
source fidelity and source-specific recipient permission; native consistency is not that check.
