---
name: operational-resilience-reporter
description: >-
  Maintain critical-service and critical-third-party registers and assemble DRAFT
  operational-resilience deliverables - incident, testing, dependency, impact-tolerance, and
  regulatory self-assessment reports - from approved registers, CMDB/dependency maps,
  incidents, tests, impact tolerances, contracts, and versioned jurisdictional templates,
  filling every required section with evidence-cited facts and deterministic tie-outs
  (chronology, impact-tolerance breach, register completeness, concentration). Use when an
  operational-resilience, TPRM, or regulatory-reporting owner needs to draft or refresh a
  resilience report or register pack for review. DRAFT-ONLY: it NEVER files or submits to a
  regulator, attests or certifies for a person or the board, makes a resilience/compliance
  determination, closes a matter, or writes any register/incident/test system of record - a
  named accountable executive and second-line reviewer must adjudicate, and any submission
  is performed by an authorized human.
license: MIT
compatibility: Amazon Quick Desktop; requires critical-service/critical-third-party register, CMDB/dependency-map, incident, resilience-testing, contract/exit-plan, and jurisdictional-ruleset/template MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (security-sensitive)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "CISO / Operational Resilience"
  aws-fsi-primary-user: "Operational resilience / TPRM / regulatory reporting"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Operational Resilience Reporter

## Purpose and outcome
Turn the firm's resilience evidence — critical-service and critical-third-party registers,
CMDB/dependency maps, incidents, scenario tests, impact tolerances, and contracts — into a
**draft** report package for the requested report type and jurisdiction. Every required
template section is filled with evidence-cited facts or flagged as a `gap` for human input;
deterministic tie-outs (incident chronology, impact-tolerance breach, register completeness,
third-party concentration) are computed and cited. The outcome is a reproducible, review-
ready draft that an accountable executive and second line adjudicate before any human files
it. The skill never files, attests, or decides.

## Use when
- "Draft our SS1/21 operational-resilience self-assessment for H1."
- "Assemble the incident resilience report for the payments outage."
- "Build the impact-tolerance / dependency / scenario-testing report for these services."
- "Refresh the critical-third-party register pack and show the completeness gaps."
- "Which required sections are still gaps, and what evidence do they need?"

## Do not use
- **Running scenario/impact-tolerance tests** → `operational-resilience-scenario-tester`.
- **Investigating an incident** (timeline, root cause) → `cyber-incident-response-coordinator`.
- **TPRM/critical-third-party risk assessment** → `third-party-cyber-risk-reviewer` /
  `third-party-risk-assessor`.
- **Filing/submitting to a regulator, attesting, or certifying** → refuse; that is a human
  act (regulatory-reporting owner / accountable executive / board).
- **Concluding compliance, closing a matter, or classifying a major incident** for the
  regulator → refuse; the skill records status and facts only.
- Unsupported jurisdictions (no configured rule pack) → stop and surface the gap.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills produce the tests,
incidents, and assessments consumed here as evidence; downstream, the draft feeds board and
exam packaging. Filing, attestation, and notification are **human** handoffs, not skills —
the package records their *status* only and never performs them.

## Inputs and prerequisites
- A resilience dataset: `report_request` (report_type, jurisdiction, template_version,
  as_of_date, reporting_period, and any notification/attestation status), `ruleset_version`,
  the critical-service register, critical-third-party register, dependency map, incidents,
  tests, and recorded approvals. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to registers, CMDB, incident and testing systems, contracts, and the versioned
  jurisdictional ruleset/templates.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The registers are the system of
record for service/third-party identity; the ruleset and templates are **versioned
contracts** (the version is recorded on the package). Cite every fact; a jurisdiction/
template mismatch is fail-closed.

## Workflow
1. **Validate & resolve** — run `validate_input`; resolve service/third-party identity for
   every incident, test, and dependency; flag unresolved identity as `needs-human-input`.
2. **Compute deterministic facts** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): incident
   durations, impact-tolerance breach (observed vs threshold by direction), register
   completeness, and third-party concentration — all explainable, all cited.
3. **Assemble required sections** — for the `report_type` + `jurisdiction`, fill every
   required section from evidence; a section with no evidence is a `gap` with a needs note,
   never fabricated content.
4. **Record human approvals** — capture the `accountable-executive` and `second-line-review`
   approvals as evidence (the skill records; humans decide).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any missing section, uncited claim, tie-out mismatch, missing approval, or
   filing/attestation/determination language.
6. **Hand off the draft** — present the package (watermarked DRAFT) for human adjudication;
   never file, submit, or attest.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces:
template fidelity (all required sections present), no unsupported claims (empty
`unsupported_claims`; drafted sections cited; gaps empty), impact-tolerance tie-outs,
required approvals recorded, the no-filing/no-attestation/no-determination language screen,
and the draft watermark + standing note. Correct and repeat until clean or fail closed.

## Human approval
`required`. A named accountable executive (first line) and a second-line reviewer must
adjudicate the draft; the package must record both as `approved` with name and date before
it is review-complete. Attestation, notification, and any regulatory submission are separate
human acts outside this skill. The skill drafts and packages; humans decide and file.

## Failure handling
- **Unresolved identity** (incident/test/dependency references an unknown service) → mark
  `needs-human-input`; do not guess the mapping.
- **Missing register fields** (IBS tolerance, critical-TP contract/exit) → report in
  `register_completeness.missing_fields`; do not fill.
- **No evidence for a required section** → emit `gap` with a needs note; never fabricate.
- **Jurisdiction/template mismatch or missing rule pack** → stop; surface the version gap.
- **Missing approvals** → output fails closed; return the draft as not-yet-adjudicated.
- **Tool timeout** → return the partial package with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Draft report package** (JSON `report_package`) — report_type, jurisdiction, template
   and ruleset versions, as_of, reporting_period, `required_sections`, and `sections[]` each
   `drafted` (cited facts) or `gap` (needs note).
2. **Impact-tolerance assessments** — per incident: metric, threshold, observed, direction,
   `breached`, citation (deterministic tie-out).
3. **Register completeness** — counts + `missing_fields`.
4. **Gaps** — every unresolved section with what it needs.
5. **Approvals recorded** — required roles with decision/name/date.
6. **Draft watermark + standing note** — "DRAFT … not filed or submitted"; the standing note.
7. Rendered per [assets/output-template.md](assets/output-template.md).
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Confidential (security-sensitive).** Registers, dependency maps, and incident detail expose
control weaknesses — mask internal identifiers to what the report requires. Retain the draft
package, citations, `ruleset_version`/`template_version`, and recorded approvals for
reproducibility. Log the author identity and every read on registers, incidents, tests, and
contracts.

## Gotchas
- **Breach ≠ determination.** "Impact tolerance breached" is a factual, deterministic
  observation and is allowed; "we are compliant / no notification required / matter closed"
  is a regulated decision and is blocked.
- **Draft ≠ filing.** Recorded approvals authorize the draft's accuracy for onward human
  handling; they do not file it. The skill never submits or attests.
- **Gaps are honest.** A section without evidence stays a `gap`; filling it with plausible
  prose is a fabricated-evidence failure.
- **Versioned templates.** Record `ruleset_version` and `template_version` on every package;
  a jurisdiction/template mismatch is fail-closed, not a best guess.
- **Status, not act.** Notification and board-attestation sections record human-provided
  *status* only — the skill never notifies a regulator or attests.
