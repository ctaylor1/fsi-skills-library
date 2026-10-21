# Native input contract

Use `evals/files/input_complete.json` for a fully synthetic instance. Runtime schema definitions
are `MANDATE` and `COLLECTIONS` in `scripts/domain.py`; input validation enforces those exact keys.
No undeclared field can carry a decision, approval, narrative or restricted-data side channel.

Top-level keys: `request_id`, `object_id`, `object_type`, `as_of`, `knowledge_cutoff`, `workflow`,
`sources`, `data`. The exact object type is `financial_crime_case_quality_review`. Foundation 2.0
requires actual workflow context, role, classification, authorized audience, registry versions,
real publication/receipt dates and globally unique source/fact IDs. Every source fact includes
`fact_id`, `value`, supplied `excerpt`. Dates are YYYY-MM-DD; cutoff <= as_of. Dates and identity
assertions are not authenticated.

`data` contains exactly:

| Object/collection | Identity | Important supplied claims |
|---|---|---|
| mandate | source-bound mandate_id | mandate type/owner/reviewer, reviewed legal profile/version/authority/scope, five independence evidence fields, period, population/selected/criterion IDs, sampling method/rationale, maximum_exception_proportion |
| cases | native_case_id | case_id must match; institution/entity/jurisdiction, upstream native ID/version, period, exhibit/concern/contradiction/counterevidence inventories, disposition reasoning ID/value/date |
| exhibits | exhibit_id | case_id, version, evidence_source_ref, evidence_fact_ids, available, captured_on |
| events | event_id | case_id, occurred_on, predecessor_event_ids, exhibit_ids, event_kind, statement |
| reasoning | reasoning_id | case_id, concern_ids, considered_counterevidence_ids, addressed_contradiction_ids, exhibit_ids, rationale, proposed_disposition, human_review_complete, reviewer_id, human_judgement |
| criteria | criterion_id | kind, version, procedure, requirement, legal_profile_id/version, applicable_case_ids |
| observations | observation_id | case_id, criterion_id/version, tested_on, observed_outcome, rationale, exhibit_ids, reasoning_ids, human_reviewer_id, human_review_complete |
| tool_outputs | output_id | case_id, tool/model/prompt/output identities and versions, generated_on, purpose, proposed_facts, exhibit_ids, named completed human review |

All fields except a collection's native identity are exact claim objects with `value`, `source_refs`
and `fact_ids`. Null substantive values with lists are valid partial intake. Unknown identities
must never be invented. String lists have distinct IDs; missing collections must be explicit empty
lists. Observation outcome and human reasoning judgment are pass/fail/unknown; boolean facts are
actual booleans. Thresholds are exact decimal strings from 0 to 1, including `"0"`/`"1"`.
`proposed_facts.value` is a list of `{source_ref, fact_id, value}` records distinct by source/fact
locator. The tool proposal itself is source-bound to the output evidence; its proposed values are
then compared to the identified underlying source fact, which remains unverified.

Native IDs, claims, aliases and criteria are not imported automatically from another package.
Retain the separate original input with its source registry and validate any upstream native
artifact against its own original before a human-reviewed field adapter creates this input.
