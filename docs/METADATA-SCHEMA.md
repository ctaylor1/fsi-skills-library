# Frontmatter & Metadata Contract

Every `SKILL.md` in this library uses the following YAML frontmatter. All spec fields obey
the [Agent Skills specification](https://agentskills.io/specification); all `metadata:`
values are **strings** (the spec requires a string→string map).

## Spec fields

| Field | Required | Value in this library |
| ----- | -------- | --------------------- |
| `name` | Yes | Must equal the skill's directory name. 1–64 chars, lowercase `a–z 0–9 -`, no leading/trailing/consecutive hyphens. |
| `description` | Yes | 1–1024 chars. States **what** the skill does **and when** to use it; includes user intents, artifacts, and domain keywords. |
| `license` | No | `MIT` (the library is MIT-licensed; see repo `LICENSE`). |
| `compatibility` | No | ≤ 500 chars. `Amazon Quick Desktop; requires <named MCP integrations / local tools / network>`. |
| `metadata` | No | The `aws-fsi-*` map below. |

## `metadata` keys (all string values)

| Key | Values / format | Source |
| --- | --------------- | ------ |
| `aws-fsi-category` | One of the 14 category display names. | Catalog |
| `aws-fsi-skill-type` | One of the six skill types (see below). | Derived (archetype + overrides) |
| `aws-fsi-risk-tier` | `R1` \| `R2` \| `R3` \| `R4`. | Build Matrix |
| `aws-fsi-archetype` | One of the 9 archetypes. | Build Matrix |
| `aws-fsi-agent-pattern` | e.g. `Interactive decision-support copilot`, `Case agent + evidence bundle`, `Plan-validate-execute workflow agent`. | Build Matrix |
| `aws-fsi-delivery-wave` | `Wave 1 — stabilize existing` \| `Wave 1 — platform controls` \| `Wave 1 — low-risk productivity` \| `Wave 2 — analytical production` \| `Wave 3 — regulated casework` \| `Wave 4 — gated orchestration`. | Build Matrix |
| `aws-fsi-action-mode` | `Read-only analysis` \| `Draft-only; no system-of-record change` \| `Scheduled read-only; alert only` \| `Approval-gated write or submission`. | Build Matrix |
| `aws-fsi-scheduled-agent` | `no` \| `read-only-monitoring`. | Build Matrix |
| `aws-fsi-baseline-status` | `new` \| `existing-updated` \| `existing-no-changes`. | Catalog |
| `aws-fsi-human-approval` | `none` \| `external-delivery` \| `required`. | RISK-TIERS.md mapping |
| `aws-fsi-data-classification` | e.g. `Confidential`, `Highly Confidential (customer NPI/PII)`, `Restricted`. | Authoring |
| `aws-fsi-jurisdictions` | Configured jurisdictions, e.g. `US (default); configure additional jurisdiction packs per deployment`. | Authoring |
| `aws-fsi-owner` | Accountable business owner role. | Authoring / Plan Updates |
| `aws-fsi-primary-user` | Primary user role(s) from the catalog. | Catalog |
| `aws-fsi-version` | Semver. Initial authoring in this repo is `0.1.0` regardless of AWS-baseline status (which is captured separately in `aws-fsi-baseline-status`). | Authoring |
| `aws-fsi-recertification-date` | `yyyy-mm-dd`. Default = one year from authoring. | Authoring |

## Skill type (`aws-fsi-skill-type`)

A coarse, cross-cutting classification of what kind of skill this is, independent of the
build archetype. One of exactly six values:

| Skill type | Meaning | Typical archetypes |
| ---------- | ------- | ------------------ |
| `Artifact-creation skills` | Produce a deliverable document/model/package | Draft & package, Model & calculate |
| `Utility skills` | Small, reusable, technical parser/transformer/tooling | (overrides) message/data transformers, skill-authoring |
| `Workflow or orchestration skills` | Coordinate a multi-step, gated process | Orchestrate & resolve |
| `System-interaction or operational skills` | Run against / coordinate live operational systems | Monitor & alert; SOC/IR ops |
| `Analysis and evaluation skills` | Apply rules/analysis to inputs, produce findings/evidence | Analyze & review, Reconcile & validate, Investigate & casework |
| `Guidance or domain-expertise skills` | Explain/advise using domain knowledge and sources | Explain & summarize, Domain workflow |

The default is derived from the archetype (see `tools/build_catalog_from_xlsx.py`
`DEFAULT_TYPE_BY_ARCHETYPE`), with a curated `SKILL_TYPE_OVERRIDES` set for skills whose
content clearly indicates a different type (e.g., `iso-20022-message-interpreter` →
`Utility skills`). The authoritative per-skill value is stored in
`catalog/skills-catalog.json`.

## Versioning note

`aws-fsi-baseline-status` records the disposition **relative to the original AWS baseline**
(`new`, `existing-updated`, `existing-no-changes`). Because this repository authors every
package fresh, `aws-fsi-version` starts at `0.1.0` for all skills and advances through the
CHANGELOG as the package is hardened and released. Do not infer a prior `1.x` from
`existing-updated`; there is no prior artifact in this repo.

## Example

```yaml
---
name: account-anomaly-screener
description: >-
  Identify unusual account activity, explain the contributing signals, and prepare
  evidence for customer or fraud-team review. Use when a consumer, service agent, or fraud
  analyst asks why a transaction or account looks unusual, or to assemble review evidence.
  Never makes a fraud determination or blocks an account.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking, CRM, document-intelligence, and approved-calculation MCP integrations.
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 — stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking fraud & customer operations"
  aws-fsi-primary-user: "Consumer / fraud analyst / service agent"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---
```
