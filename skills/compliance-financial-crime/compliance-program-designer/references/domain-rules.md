# Domain method and schema

The native method links mandates → risks → controls → accountability → resources. For each risk it reports controls, missing design/dependency evidence and unassigned accountability. Required/allotted resource facts produce a supplied-unit difference only when both are supported, finite, nonnegative and comparable. Missing mandate, risk coverage or resourcing is visible; no organization-wide compliance conclusion is calculated.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`mandates`: nonempty records `{id, scope_fact, owner_fact}`. `risks`: nonempty `{id, category, exposure_fact, mandate_ids}`. `controls`: records `{id, risk_ids, design_fact, process_fact, system_fact, data_fact, evidence_fact, owner_fact}`. `accountability`: `{role, mandate_fact, escalation_fact, independent_testing_fact}`. `resources`: `{id, unit, scope, required_fact, allocated_fact}`. All `*_fact` fields are claims `{value, source_refs, fact_ids}` resolved against exact registry facts.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?
