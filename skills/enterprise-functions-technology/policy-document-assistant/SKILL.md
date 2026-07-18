---
name: policy-document-assistant
description: >-
  Draft, compare, explain, and maintain controlled policies and procedures from an approved
  requirements register: assemble a controlled deliverable (document control, sourced policy
  statements, roles, version history, recorded approvals), map every normative statement to an
  approved requirement, compute the next version and review date, and summarize changes against
  the prior version. Use when a policy owner, legal, compliance, or operations needs to draft a
  new policy or procedure, amend or version an existing one, compare two versions, or explain
  what an approved policy requires and where each statement comes from. HARD BOUNDARY: draft-only
  — it never publishes, activates, files, or makes a policy effective, never writes the
  policy/content system of record, never asserts a normative requirement without an approved
  source, never records or backdates its own approvals, and gives no personalized legal advice;
  owner/legal/compliance approval and publication are separate human actions.
license: MIT
compatibility: Amazon Quick Desktop; requires approved-requirements-register, controlled-content-library, approved-source-retrieval, document-intelligence, and entity-resolution MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "Policy owner / legal / compliance / operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Policy Document Assistant

## Purpose and outcome
Turn an approved set of requirements into a **controlled policy or procedure draft** that is
ready for human review: a document with the required control sections, every normative
statement mapped to an approved requirement, a correctly computed version and next-review
date, a change summary against the prior version, and open approval slots. The outcome is a
faithful, source-mapped, audit-ready **draft** — the owner, legal, and compliance decide,
record their approvals, and publish. The skill never makes a policy effective.

## Use when
- "Draft a new [policy/procedure] from these approved requirements."
- "Amend / re-version this policy and show what changed."
- "Compare version 2.3 with this draft — what was added, modified, removed?"
- "Explain what this approved policy requires and cite where each statement comes from."
- "Assemble the CIP policy draft for review with owner/legal/compliance approvals."

## Do not use
- **Regulation-vs-policy / operations gap analysis** → `policy-procedure-gap-analyzer`.
- **Mapping a regulatory change** to affected policies/controls/owners →
  `regulatory-change-impact-analyzer`.
- **Extracting obligations from contracts** → `contract-obligation-extractor`.
- **Board/committee decision pack** for an approved policy → `board-committee-pack-builder`.
- **Publishing/activating** a policy, setting its real effective date, or writing the
  content system of record → human/operations (this skill is draft-only).
- **Personalized legal advice** or a binding regulatory interpretation → licensed counsel.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream, regulatory-change and gap
analyses seed the requirements this skill drafts against; downstream, the draft feeds gap
re-checks, committee packs, and exam-response packaging. This skill emits a **draft + source
mapping + change summary**; it does not perform the adjacent analyses or publish.

## Inputs and prerequisites
- A **policy build request**: the approved `requirements_register`; the `policy` metadata
  (id, title, type, tier, current version, change type, owner, classification, proposed
  effective date); the `clauses` (each with heading, `section_id`, text, and — for normative
  clauses — the `req_ids` that support them); optionally `prior_clauses` and `prior_version_ref`
  for the change summary; and `approvals_required`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the requirements register, controlled content library (prior version),
  approved-source retrieval, and the versioned policy-standard config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **approved requirements
register** is the only citable basis for normative statements; the controlled content library
holds the prior version of record; approved-source retrieval holds the regulation/standard
text. Cite every normative statement as `{system}:{ref}@{version/date}`. The register and the
policy-standard config are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run [scripts/validate_input.py](scripts/validate_input.py);
   confirm required fields, that normative clauses carry `req_ids`, and surface data gaps
   (missing sources, non-approved requirements, missing prior version) as warnings.
2. **Resolve sources** — map each normative clause's `req_ids` to `approved` register
   entries; any clause without an approved source becomes an **unsupported assertion** and is
   recorded, never silently accepted.
3. **Assemble the draft (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): lay clauses into
   the canonical template sections, compute the next version from the change type, compute the
   next-review date from the tier cadence, and build the change summary vs the prior version.
4. **Fill the template** — render into [assets/output-template.md](assets/output-template.md),
   keeping every required section and every clause-to-source citation.
5. **Open approvals** — create a pending slot per required role. Approvals are **recorded by
   the human approvers**, never by the skill.
6. **Never publish** — no activation, filing, effective-dating, or system-of-record write.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. Output validation enforces: all required sections present; every normative clause maps
to an approved source (no unsupported assertions); each required approval recorded; version
and next-review date tie out to the rules; no publication/activation/filing language; standing
note present. Fail closed on any miss — correct and re-run until clean.

## Human approval
`external-delivery`. The draft is not deliverable until owner, legal, and compliance are
recorded as `approved` (approver + date). Recording approvals, setting the real effective
date, and publishing into the system of record are **human** actions. This skill proposes and
assembles; humans approve and publish.

## Failure handling
- **Unsupported normative clause** (missing/non-approved requirement) → record it, block
  release, and request the approved requirement; never fabricate a source.
- **Missing prior version** → still draft, but flag the change summary as limited (no diff).
- **Ambiguous owner / requirement identity** → surface for confirmation; do not guess.
- **Superseded / expired requirement cited** → flag and exclude; request the current one.
- **Stale prior-version copy** → re-read the current version of record before diffing.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no
  automatic retry.

## Output contract
1. **Controlled policy draft** — the template sections (document control, purpose, scope,
   policy statements, roles, related documents/source mapping, review & version history,
   approvals), every normative statement cited.
2. **Source mapping** — per normative clause: `req_ids` → approved citations.
3. **Change summary** — added / modified / removed clause IDs and counts vs the prior version.
4. **Version & review** — computed `new_version` and `next_review_date` with the rule used.
5. **Approvals block** — required roles with recorded status (pending until humans sign).
6. **Machine-readable** — the assembled draft JSON keyed by `policy_id` + `new_version`.
7. **Standing note** — "Draft policy for human review only; not published, activated, or made
   effective. Owner, legal, and compliance approval and publication into the policy management
   system of record are separate human actions."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Confidential.** Drafts may expose control thresholds and named owner roles; share only with
the review chain. Retain each draft with its requirements-register version, policy-standard
config version, source mapping, change summary, and recorded approvals so the deliverable is
reproducible and auditable. Log author identity and every approval.

## Gotchas
- **Draft ≠ effective.** Recording approvals is not activation; publication and the real
  effective date are separate human/operations steps. Never imply a policy is live.
- **No requirement, no clause.** A "shall/must" statement without an approved requirement is
  an unsupported assertion — it blocks release; do not paraphrase a regulation to fill the gap.
- **Editorial changes don't bump the version.** Only `major`/`minor` change the version;
  editorial edits are logged in history at the same version.
- **Review date is proposed.** It is computed from the *proposed* effective date; the owner
  sets the real one at activation.
- **Compare uses `clause_id` + text.** Renaming a clause_id reads as a remove + add; keep IDs
  stable across versions for a meaningful diff.
- **Approved-source config is versioned.** Record the register and policy-standard versions on
  every draft so the computed version, review date, and citations are reproducible.
