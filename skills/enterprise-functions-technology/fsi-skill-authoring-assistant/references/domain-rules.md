# Domain Rules — fsi-skill-authoring-assistant

The build-standard logic applied by
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). All values are
a **versioned contract** (`build_standard_version`); the defaults below mirror this repo's
`docs/BUILD-STANDARDS.md`, `docs/METADATA-SCHEMA.md`, `docs/ARCHETYPES.md`, and
`docs/RISK-TIERS.md` and must be confirmed against the current standards at deployment. This
reference authors and validates skill packages; it does not publish, register, or approve
them.

## Required package components (by archetype + tier)

Always required (every skill):

`SKILL.md`, `references/source-map.md`, `references/controls.md`, `references/handoffs.md`,
`scripts/validate_input.py`, `scripts/validate_output.py`, `evals/evals.json`, `CHANGELOG.md`.

Conditionally required:

| Add component | When |
| ------------- | ---- |
| `assets/output-template.*` | archetype is **Draft & package** (the approved deliverable template). |
| `scripts/calculate_or_transform.*` | archetype is **Model & calculate** or **Reconcile & validate**, or the skill has deterministic computation (`has_deterministic_computation`). |
| `references/domain-rules.md` | the skill applies domain rules/thresholds/calculations (`applies_domain_rules`) or archetype is **Analyze & review**, **Model & calculate**, or **Reconcile & validate**. |

An unknown archetype yields `needs-data` (map it to the build matrix first); components are
never inferred on a guess.

## Frontmatter metadata contract

Required `aws-fsi-*` keys (all string values): `aws-fsi-category`, `aws-fsi-skill-type`,
`aws-fsi-risk-tier`, `aws-fsi-archetype`, `aws-fsi-agent-pattern`, `aws-fsi-delivery-wave`,
`aws-fsi-action-mode`, `aws-fsi-scheduled-agent`, `aws-fsi-baseline-status`,
`aws-fsi-human-approval`, `aws-fsi-data-classification`, `aws-fsi-jurisdictions`,
`aws-fsi-owner`, `aws-fsi-primary-user`, `aws-fsi-version`, `aws-fsi-recertification-date`.

Allowed-value sets enforced deterministically: `aws-fsi-risk-tier` ∈ {R1,R2,R3,R4};
`aws-fsi-action-mode` ∈ {Read-only analysis; Draft-only; no system-of-record change;
Scheduled read-only; alert only; Approval-gated write or submission};
`aws-fsi-human-approval` ∈ {none, external-delivery, required}; `aws-fsi-scheduled-agent` ∈
{no, read-only-monitoring}. `name` must equal the directory basename and match the spec name
pattern.

## Tier / action-mode / human-approval consistency (RISK-TIERS.md)

1. **R1 / R2** → human-approval `external-delivery`; action-mode `Read-only analysis` or
   `Draft-only; no system-of-record change`. No binding decision.
2. **R3** → human-approval `required`; action-mode read-only, draft-only, or scheduled
   read-only; never approval-gated write (that is R4).
3. **R4** → human-approval `required`; action-mode `Approval-gated write or submission`.
4. `read-only-monitoring` scheduled posture is permitted **only** for the **Monitor & alert**
   archetype; all other skills declare `no`.

Any violation yields `metadata-incomplete`; the package is not assembled on an inconsistent
frontmatter.

## Human approvals owed (by tier)

| Tier | Approvals required before release |
| ---- | --------------------------------- |
| R1, R2 | product-owner, domain-sme, control-owner |
| R3 | product-owner, domain-sme, control-owner, legal-compliance |
| R4 | product-owner, domain-sme, control-owner, legal-compliance, model-risk |

A **readiness claim** (e.g., "control review complete") is `supported` only when it cites a
recorded approval whose status is `complete`/`recorded`/`approved`. An unbacked claim →
`unsupported-claim`; the package is not assembled. This skill enumerates the approvals owed
and marks them **pending** — it never records or grants an approval itself.

## Status precedence

`needs-data` (spec/metadata incomplete) → `metadata-incomplete` → `missing-components` →
`unsupported-claim` → `draft-package`. Only `draft-package` is `packageable` (ready for owner
review — approvals still owed).

## What the rules never do

- No **publish / register / release** of a skill into the catalog and no catalog write.
- No **self-approval** — the skill never marks its own output validated, approved, or released.
- No **fabrication** of metadata, sources, evaluations, or approval records — a gap is
  reported, never invented.
