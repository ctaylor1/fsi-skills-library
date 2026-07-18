# Source Map — ai-use-case-intake-classifier

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **AI-governance policy / ruleset** (versioned) | Classification factors, thresholds, tier and path mapping | Read-only |
| 2 | **Intake submission** (the use-case form) | The declared facts being classified | Read-only |
| 3 | **Model registry** | Corroborate model type, ownership, lineage, prior classification | Read-only |
| 4 | **Data catalog** | Corroborate data classification, personal / special-category flags, scale | Read-only |
| 5 | **Jurisdiction / regulatory packs** | Jurisdiction-specific obligations and restricted-jurisdiction list | Read-only |

Never trust the submitter's self-declared attribute over the authoritative catalog. If the intake
and the model registry / data catalog conflict (e.g., declared "internal" but catalog says
"highly-confidential NPI/PII"), cite both and classify at the **more conservative** value, flagging
the conflict for human adjudication.

## Citation format

- Intake facts: `intake:{use_case_id};field={field}@{as_of}` — e.g.
  `intake:UC-2026-0142;field=decision_effect@2026-07-15`.
- Ruleset provenance: `policy:{ruleset}@{version}` — e.g. `policy:ai-intake@ai-intake-cfg-2026.07`.

Every fired factor cites the specific intake field(s) it read and the ruleset/version applied.

## Freshness / effective dates

- The **ruleset** (factors, thresholds, tier/path mapping) is a **versioned contract**; the output
  records the `config_version` used so a classification is reproducible. If the ruleset is expired,
  flag it — do not silently substitute a newer version.
- The output records `as_of`; re-running with the same submission and config reproduces the tier.

## Least-privilege operations (deployment)

- `policy.get('ai-intake', version)` → factor definitions, thresholds, tier/path mapping.
- `registry.lookup(use_case_id | model_id)` → model type, owner, lineage, prior classification.
- `catalog.classification(dataset_ref)` → data classification, personal / special-category flags.
- `jurisdiction.pack(code)` → obligations + restricted-jurisdiction membership.

All read-only, deterministic, durable `classification_id`, below the fixed timeout. This skill makes
no writes and stages nothing for execution.
