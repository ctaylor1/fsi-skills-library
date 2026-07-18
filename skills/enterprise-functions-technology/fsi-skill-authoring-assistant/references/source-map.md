# Source Map — fsi-skill-authoring-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Build standards & metadata schema** (this repo's `docs/`, versioned) | Required components, frontmatter contract, allowed values, tier/action-mode/approval mapping | Read-only |
| 2 | **Skills catalog** (`catalog/skills-catalog.json`, versioned) | Approved name, category, primary user, archetype, tier, description for the target skill | Read-only |
| 3 | **Approved domain artifacts / knowledge systems** | The domain rules, thresholds, sources, and procedures the drafted skill will encode | Read-only |
| 4 | **Controlled template & content library** | The `assets/output-template.*`, standing disclaimers, and body-section scaffolds | Read-only |
| 5 | **Developer tooling** (repo, `tools/validate_skills.py`, `tools/run_selftests.py`) | Specification + self-test validation of the drafted package | Read-only |
| 6 | **Project tracking / approval records** | The human approvals owed and recorded (owner, SME, control, legal, model-risk) | Read-only |

The build standards, metadata schema, and catalog are a **versioned contract**
(`build_standard_version`). Never hard-code a component list, allowed value, or approval set
that contradicts the current standards; record the version on every plan.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `build-standards:component-matrix@fsi-build-2026.07`,
`catalog:loan-covenant-checker@2026-07-17`, `metadata-schema:aws-fsi-risk-tier@v2`,
`approvals:APP-DR-1=domain-sme;status=complete@2026-07-15`.

## Freshness / effective dates

- Component matrix, metadata schema, and allowed values are read from the **current** build
  standards; a superseded standard can change both required components and allowed values.
- The catalog is authoritative for the target skill's name, category, and primary user; a
  drafted frontmatter that contradicts the catalog is a fail-closed conflict.
- Compute against a stated `as_of_date`; if none is supplied the system date is used and the
  plan must say so.

## Least-privilege operations (deployment)

- `standards.get(component_matrix|metadata_schema, version)` → required components, allowed
  values — read-only.
- `catalog.get(skill_name)` → approved name/category/primary user/archetype/tier — read-only.
- `knowledge.get(artifact_id)` / `templates.get('output-template', version)` — read-only,
  bounded.
- `approvals.get(skill_id)` → recorded human approvals and their status — read-only.
No mutation from this skill. Publishing, registration, and catalog writes are **out of
scope** — performed by an authorized human/release pipeline after review and approval.
