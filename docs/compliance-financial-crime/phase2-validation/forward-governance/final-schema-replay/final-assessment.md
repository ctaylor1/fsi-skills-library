# Independent final governance schema replay

**Sampled schema/native checks pass.** This is the third separately saved governance assessment. It does not overwrite the initial forward failures, the first repaired-code replay or its output-schema failures.

Eight preserved casework intakes and eight actual current native replay outputs were checked with **jsonschema 4.26.0 Draft202012Validator** against the four current companion input/output schemas. All schemas pass check_schema. Every output was also revalidated by its current native CLI against the separately retained original input.

## Positive checks

Input schema compatibility: **8/8**. Output schema compatibility: **8/8**. Native detached output revalidation: **8/8**.

| Preserved case | Current input schema | Current output schema | Native output validation |
|---|---|---|---|
| 11-sanctions-exact50 | PASS | PASS | PASS |
| 12-sanctions-below50 | PASS | PASS | PASS |
| 13-sanctions-indirect | PASS | PASS | PASS |
| 14-sharing | PASS | PASS | PASS |
| 15-typed-reporting | PASS | PASS | PASS |
| 16-notification-immediate | PASS | PASS | PASS |
| 17-notification-isolation | PASS | PASS | PASS |
| 18-notification-isolation-reordered | PASS | PASS | PASS |

These cases include sourced object perimeter and boolean sanctions conditions; exact near-50 ownership strings; unsupported indirect ownership producing null amount; SAR existence and unnecessary content withheld as null; exact currency amount/threshold strings and null mixed-currency amount/trigger; string materiality facts, immediate duty with null deadline, and missing channel. The schemas now preserve these actual types and unresolved branches rather than requiring conversions or fabricated defaults.

## Targeted rejection checks

Four representative outputs were independently mutated after the complete pre-audit expectations were saved. Each mutation is retained as its own JSON file with schema errors, exact native command, native return code and validator stdout/stderr.

- **48/48 malformed authority/context/computed-type mutations** are rejected by both the companion output schema and exact native reconstruction: **96/96 rejection checks**. Mutations cover action/approval/execution/source-authentication claims, bypassing human review/draft state, blank/missing/wrong-type context, floating computed monetary amounts, string/numeric computed booleans, nonstring item kind and nonarray matched permission IDs.
- **4/4 well-typed legal-entity context substitutions** are structurally accepted by JSON Schema and rejected by exact native original-input reconstruction: **8/8 expected checks**. A structural schema cannot authenticate context equality against a detached original; the native validator supplies that bound check.
- Total targeted mutation expectations: **104/104** pass, with no unexpected acceptance or rejection.

## Source and evidence stability

All **36** tracked current schema/runtime source files match the corresponding hashes in root's **6,874-file** source freeze. All 36 hashes remain stable before/after the audit. Every prior governance artifact hash remains unchanged, including initial inputs, pre-run expectations, exact outputs, frozen code/schema snapshots, initial **147/150** score, initial **8/8 input-schema incompatibilities**, original notification failure replays, evaluator arithmetic correction, repaired-code **60/60 CLI / 150/150 expectation** report, and subsequent **0/8 companion output-schema** failure evidence. The latter remains a historical failing snapshot, not the current schema result.

This evaluator changed no package, shared module, catalog or root-owned document. Saved evidence is confined to final-schema-replay/.

## Results and limits

No real failure remains in this final eight-case schema/native audit. This adds schema compatibility and bounded rejection evidence to the previously passing twenty-case native replay. It does not establish source authenticity, current-law completeness, institution-specific applicability, legal/professional acceptance, representative operational populations, model interpretation quality, independent assurance, receiver compatibility, deployment readiness or live action. No filing, notification, disclosure, launch, system update, commit or external message occurred.

Files: pre-audit-expectations.json; audit-results.json; schema-and-native-hashes-before.json; original-artifact-hashes-before.json; schemas/; per-case native stdout/stderr; mutations/ with every modified output and replay result. Exact command/interpreter/validator versions, input/output/source hashes and error paths are retained in audit-results.json.
