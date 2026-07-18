# Adjacent-Skill Handoffs — fsi-skill-authoring-assistant

This skill is the **skill engineering copilot**: it drafts and validates FSI Agent Skill
packages for a human to review, approve, and release. It authors artifacts; it does not
exercise the authored skill's domain judgment, and it does not publish or register anything.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| Portfolio governance / product owner | Approved skill spec: name, category, archetype, tier, primary user, description intent, boundary | `skill_id` + spec card |
| Build standards & metadata schema (`docs/`) | Required components, frontmatter contract, allowed values, tier mapping | `build_standard_version` |
| Skills catalog (`catalog/`) | Approved name, category, primary user for the target skill | catalog entry |
| Approved domain artifacts / SMEs | The domain rules, thresholds, and sources the drafted skill encodes | source references |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Exercising a domain task (triage an alert, reconcile a ledger, price a trade, adjudicate a claim) | the relevant **domain skill** — this skill authors packages, it does not run them |
| Publishing / registering a skill into the catalog or a system of record | the **release pipeline / catalog owner** (authorized human) |
| Approving a package (owner, domain SME, control, legal, model-risk sign-off) | the **named human approver** — approval is never granted by this skill |
| Building the catalog itself from the source spreadsheet | `tools/build_catalog_from_xlsx.py` (repo tooling, run by a maintainer) |

## Downstream (human / pipeline, not a skill)

The reviewed and approved package is published/registered by an **authorized human or release
pipeline** after `validate_skills.py` and `run_selftests.py` pass and the required approvals
are recorded. This skill emits a `skill_id`-keyed authoring plan plus an approval checklist
and a `reviewer_signoff_required` posture; it must not perform the release.

## Duplicate-execution prevention

- This skill **does not** publish, register, approve, or exercise the authored skill — those
  belong to the routes above or to a human/pipeline.
- A plan carries the `skill_id` and `build_standard_version` so a reviewer works one authored
  draft rather than re-scaffolding.
- A `needs-data`, `metadata-incomplete`, `missing-components`, or `unsupported-claim` record
  is resolved by a human (complete the spec / add the component / record the approval), never
  force-packaged.
