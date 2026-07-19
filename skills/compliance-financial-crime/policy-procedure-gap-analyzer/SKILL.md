---
name: policy-procedure-gap-analyzer
description: >-
  Compare an organization's internal policies and procedures against authoritative
  requirements (laws, regulations, supervisory guidance, standards) and against actual
  operations, and produce cited findings — coverage gaps, parameter conflicts,
  obsolete/version-drift steps, evidence gaps, and stale reviews — each with a remediation
  recommendation and a deterministic severity. Use when a compliance advisor, policy owner,
  or auditor asks "where does our policy not cover this rule", "does our procedure conflict
  with the regulation", "which steps are obsolete", "what evidence is missing", or needs a
  gap-analysis pack for a policy refresh, exam prep, or issue log. HARD BOUNDARY: this skill
  evidences and recommends only; it NEVER states or implies the firm is compliant,
  attests/certifies, closes a finding, signs off remediation, files or submits to a
  regulator, or rewrites the policy system of record — those require human adjudication (R3).
license: MIT
compatibility: Amazon Quick Desktop; requires regulatory-corpus, controlled-content-library (policies), records-archive/case-management, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "Compliance advisory / policy owner / audit"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Policy & Procedure Gap Analyzer

## Purpose and outcome
Given a set of authoritative **requirements** (laws, regulations, supervisory guidance,
standards) and the organization's internal **policy/procedure controls** that claim to
satisfy them, deterministically map controls to requirements and surface **explainable
findings** — coverage gaps, parameter conflicts, obsolete/version-drift steps, evidence
gaps, and stale reviews. Each finding carries cited evidence, a deterministic severity, and
a remediation **recommendation**. A successful output lets a compliance advisor, policy
owner, or auditor see exactly where policy diverges from requirement (or from actual
operations) and what to fix — the compliance judgment, remediation, and any filing remain
human.

## Use when
- "Where does our policy not cover this rule / regulation / standard?"
- "Does our procedure conflict with the requirement (thresholds, retention, frequency)?"
- "Which procedure steps are obsolete after the rule changed?"
- "What evidence is missing to show this control operates?"
- Building a gap-analysis pack for a policy refresh, exam preparation, or an issue log.

## Do not use
- The user wants a **compliance determination**, **attestation**, **remediation sign-off**,
  a **finding closed**, or a **regulatory filing** → out of scope. Provide findings and
  route to the accountable compliance officer / policy owner / internal audit.
- The user wants the **impact of a new/changed regulation itself** (what changed, where it
  applies) → `regulatory-change-impact-analyzer` (may feed this skill).
- The user wants to **draft or rewrite** the corrected policy/procedure →
  `policy-document-assistant`.
- The user wants to **package an exam response** or **collect the evidence artifact** →
  `regulatory-exam-response-packager` / `audit-evidence-packager`.
- The user wants an **RCSA** or an **enterprise risk assessment** →
  `risk-control-self-assessment-assistant` / `enterprise-risk-assessment-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a gap-analysis pack
with a durable `analysis_id`; upstream change/obligation skills feed it, and downstream
drafting/packaging/RCSA skills consume its findings. It must not duplicate their drafting,
attestation, or filing steps.

## Inputs and prerequisites
- **Requirements** for the framework/jurisdiction in scope: each with `req_id`, source,
  citation, obligation text, `criticality` (`mandatory`|`guidance`), `effective_date`,
  `version`, `evidence_expected`, and an optional structured `parameter` (kind + value).
- **Policy/procedure controls**: each with `control_id`, doc/section, `maps_to` (requirement
  ids), `status` (`active`|`retired`), `last_reviewed`, optional `references_version`,
  `evidence_ref`, and an optional structured `parameter`.
- `as_of` date and the versioned `config` (review window, comparators, mapping). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the regulatory corpus, controlled policy library, and records archive.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **regulatory corpus is the
requirement of record**; an internal policy never overrides it. When policy and requirement
conflict, cite both and raise a finding; when the documented procedure and observed
operations conflict, cite both for the reviewer to adjudicate.

## Workflow
1. **Scope** — confirm the framework/jurisdiction, `as_of`, and `config_version`; load the
   in-effect requirements and the mapped policy/procedure controls.
2. **Validate input** — run `validate_input`; resolve structural errors, note evaluability
   warnings (unknown mappings, missing evidence flags, uncovered requirements).
3. **Compute findings (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to map controls to
   requirements and emit findings (`coverage_gap`, `parameter_conflict`, `evidence_gap`,
   `version_drift`, `stale_review`), each with evidence, a deterministic severity, and a
   recommendation. Requirements not yet in effect or not applicable are reported as
   informational, never gaps; unmatched parameter kinds are `not_evaluable`, never passed.
4. **Assemble the pack** — findings + cited evidence + severity_counts + a triage
   `remediation_priority`, plus the clean requirements, informational items, and reviewer
   prompts (documented-vs-actual operations, pending exceptions, accepted risks).
5. **Write the narrative** — plain-language summary per severity band, each finding's reason
   and recommendation, explicit uncertainties, and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check (the R3 prohibited-decision screen) confirms: every finding has
cited evidence; each severity equals the deterministic mapping; counts and priority tie out;
**no determination/attestation/closure/filing language** is present; and the standing
disclaimer is included. Fail closed on any miss.

## Human approval
`required` (R3): a human must adjudicate every finding before any regulated decision,
remediation sign-off, attestation, filing, or system-of-record change. No approval is needed
for the reviewer's own read of the pack. The skill never decides, closes, drafts the
remediated policy, attests, or files.

## Failure handling
- **Missing/duplicate ids or bad dates** → `validate_input` fails closed; stop and fix.
- **Mapping references an unknown requirement** → warn and ignore that mapping; do not
  fabricate coverage.
- **Requirement parameter with no matching control parameter** → report `not_evaluable`; do
  not assume the control satisfies it.
- **Requirement not yet in effect / not applicable** → informational only; never a gap.
- **Stale or conflicting sources** → cite both (corpus and policy); never silently reconcile.
- **Tool timeout / long corpus** → return findings computed so far with an "incomplete" flag
  and the requirements not yet evaluated; page as resumable stages.

## Output contract
1. **Summary** — framework, `as_of`, severity_counts (High/Medium/Low), `remediation_priority`.
2. **Findings** — per finding: `finding_type`, `req_id`/`control_id`, severity, plain-language
   reason, cited evidence rows, and a remediation recommendation.
3. **Clean / informational / not-evaluable** — covered requirements, not-yet-effective or
   inapplicable requirements, and unmatched-parameter cases (transparency, not silence).
4. **Reviewer prompts** — documented-vs-actual operations, pending exceptions, accepted risks.
5. **Machine-readable** — findings + evidence + `analysis_id` + `config_version` for
   downstream skills and reproducibility.
6. **Standing disclaimer** — "Gap-analysis findings and recommendations only; not a
   compliance determination, attestation, or filing. Human adjudication required."
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted (AML/BSA — SAR confidentiality; tipping-off controls). Do not reproduce SAR
contents or name subjects; reference records by pointer, not payload. Paraphrase regulatory
text (short) rather than reproducing it. Minimize data to what evidences a finding. Retain
the analysis + citations + `config_version` per records policy; log the read and the human
adjudication decision.

## Gotchas
- **A finding is not a determination.** Gaps and conflicts justify *review and remediation
  planning*, never a statement that the firm is (non-)compliant. That conclusion is human.
- **Retired controls do not count as coverage.** A requirement mapped only to a retired
  control is a coverage gap — do not credit inactive documents.
- **Weaker parameters are conflicts even when a control "exists".** A retention period below
  the minimum or a reporting threshold above the maximum is a real gap, not a match.
- **Version drift = obsolete steps.** A control citing a superseded requirement version
  likely contains obsolete procedure steps; flag it even if the topic is "covered".
- **Guidance vs mandatory changes severity, not existence.** A guidance-level gap still fires;
  it is simply one band lower. Do not suppress it.
- **Do not tune the config to erase a gap.** Comparators, the review window, and the severity
  mapping come from the versioned config, never from what would make a finding disappear.
