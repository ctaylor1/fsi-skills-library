# Domain method and schema

The native method builds a dependency graph and rejects unknown references, self-dependencies and cycles. A dependency is satisfied only with supported complete status, supported evidence matching exact release scope, and satisfied predecessor dependencies. Blocked/incomplete/unknown dependencies or cross-scope evidence propagate into release blockers. Exception evidence is recorded but never silently converts a legal applicability/permission blocker into launch authorization. The result is a release review state, not readiness approval.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`change`: `{id, baseline_scope, target_scope, scope_fact}`. `releases`: nonempty `{id, scope, planned_date, dependency_ids}`. `dependencies`: nonempty `{id, kind, scope, status_fact, evidence_fact, owner_fact, requires}`. `exceptions`: optional `{dependency_id, release_id, rationale_fact, authority_fact}`. Kind is `applicability|permissions|policy|process|control|system|data|training|resources|specialist`; exact scope structures must match.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?

`scope_fact.value` must exactly equal the change target scope. Dependency `evidence_fact.value` exactly equals `{dependency_id, scope, status}` for the release. Optional release `actual_start_fact` contains a date, `not_started`, or unknown; dependency `effective_date_fact` and `compliance_date_fact` preserve supplied dates separately. Exact JSON scope comparisons keep booleans distinct from numbers. Different staged release subscopes remain open for scoped human review rather than inheriting broad target approval.
