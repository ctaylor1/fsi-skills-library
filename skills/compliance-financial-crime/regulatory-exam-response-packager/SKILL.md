---
name: regulatory-exam-response-packager
description: >-
  Assemble a controlled regulatory examination or inquiry response package: map each regulator
  request to its drafted narrative and evidence, verify every assertion is sourced, compute
  per-request coverage and readiness, report issue/MRA status, and confirm the required human
  approvals are recorded — following a fixed response template. Use when regulatory affairs,
  compliance, or legal needs to organize an exam/inquiry request list, document/PBC requests,
  findings or MRA responses, evidence, narratives, approvals, and provenance into an
  audit-ready draft package. HARD BOUNDARY: draft-only — this skill NEVER submits or sends the
  response to a regulator, closes or resolves an exam item/finding/MRA, makes a regulated
  attestation or certification, presents an unsupported or unapproved claim as ready, or writes
  any system of record. Gaps and missing approvals are surfaced; a human owns review and
  submission.
license: MIT
compatibility: Amazon Quick Desktop; requires case-management (exam workspace), records-archive/document-intelligence, regulatory-corpus, KYC/AML, sanctions/PEP, transaction-monitoring, and approval-broker MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "Regulatory affairs / compliance / legal"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Regulatory Exam Response Packager

## Purpose and outcome
Turn a regulator's examination or inquiry request list into a controlled, audit-ready **draft
response package**. For each request, map the drafted narrative and evidence, confirm every
assertion is sourced, compute a documented coverage/readiness status, report issue/MRA status,
and confirm required human approvals are recorded — all rendered against a fixed template. The
outcome is a package a human reviewer can trust and submit: complete items are marked ready,
and every gap, missing evidence, unsupported assertion, and missing approval is surfaced, not
hidden. This skill assembles and checks; it never submits, closes, attests, or writes a system
of record.

## Use when
- "Package our response to the OCC/FDIC/SEC/FINRA/CFPB exam request list."
- "Organize the PBC / document requests, narratives, and evidence into a response pack."
- "Draft the response to these exam findings / MRAs and show what still needs approval."
- "Which request responses are ready, and which have gaps or unsourced claims?"

## Do not use
- **Substantive analysis** feeding a response (investigate an alert, adjudicate a sanctions
  match, rate customer risk) → the upstream skills in [references/handoffs.md](references/handoffs.md).
- **SAR drafting** → `suspicious-activity-report-drafter` (draft-only, human-filed).
- Any request to **submit/send the response, close an exam item, or attest on the firm's
  behalf** → refuse; that is a human, authorized action.
- Jurisdictions without a configured pack → stop and request configuration.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill sits **downstream** of the
evidence-producing skills and **upstream of a human** (regulatory affairs / compliance / legal)
who reviews and submits. It cites upstream `case_id`s / evidence rather than re-deriving them,
and never performs the human submission step.

## Inputs and prerequisites
- The exam/inquiry request set: `exam{exam_id, regulator, scope, period}`, `requests[]` (id,
  prompt, category, `evidence_required`, due date), the drafted `responses[]` (narrative,
  `assertions[]` each with a `source_ref`, `evidence[]` with provenance, `issue_status`,
  `approvals[]`), and `required_approver_roles`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to case-management, records-archive/document-intelligence, regulatory corpus, and
  the approval broker.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case-management is the system of
record for exam/item **state**; the records archive for the **evidence** cited. Cite every
assertion and evidence item with `{system}:{ref}@{date/version}`. The template + required
approver config is a **versioned contract**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm requests are well-formed, every
   response maps to a known request, and every evidence item carries provenance. Warnings mark
   the gaps/unsupported items the package will surface.
2. **Map requests to responses** — join each request to its response; unmatched requests become
   `gap` items (never fabricated).
3. **Compute coverage & readiness (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per request derive
   coverage (`complete` | `partial` | `needs-evidence` | `gap`) and response status
   (`draft-ready-for-review` | `needs-approval` | `unsupported-assertion` | `needs-evidence` |
   `incomplete`) from the documented rules in [references/domain-rules.md](references/domain-rules.md).
4. **Assemble the package** — render all ten sections of
   [assets/output-template.md](assets/output-template.md): identification, scope, request-response
   index, narratives (each assertion cited), evidence register, issue/MRA status, approvals,
   source map, outstanding items, and draft-status note.
5. **Validate output** — run `validate_output`; fail closed on any missing section, unsupported
   or unapproved item marked ready, submission/closure/attestation language, or wrong readiness.
6. **Never submit or close** — hand the reviewed draft to the human owner; submission and any
   exam-item state change are theirs.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all ten template sections present; only allowed coverage/status
values; no unsupported assertion or missing approval inside a ready item; a ready item is
cited; `readiness == "draft-not-submitted"`; no submission/closure/regulated-decision language;
standing note present. Fail closed on any miss.

## Human approval
`required`. This skill records approvals; it does not grant them. An item is `draft-ready-for-review`
only when all `required_approver_roles` are recorded as `approved`. Submission to the regulator,
closure of any exam item/finding/MRA, and any regulated attestation are human, authorized
actions — this skill proposes and packages; humans decide and submit.

## Failure handling
- **Missing response / evidence** → set `gap` / `needs-evidence` and list exactly what is
  needed; never fabricate a response to fill a request.
- **Unsourced assertion** → mark the item `unsupported-assertion`; do not present it as ready.
- **Missing approval** → mark `needs-approval`; the item is not ready regardless of content.
- **Stale/conflicting evidence** → cite the effective date/version; surface the conflict, do
  not silently pick one.
- **Unknown jurisdiction / no config** → stop; request the jurisdiction pack and approver config.
- **Tool timeout** → return the partial package with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Request-response index** — per request: `request_id`, coverage, response status, and the
   short prompt.
2. **Response narratives** — per request, each factual assertion carrying an inline citation.
3. **Evidence register** — each item with `evidence_id`, description, source_ref, classification.
4. **Issue/MRA status, approvals, source map** — reported, with the required-approver check.
5. **Outstanding items and gaps** — every gap / missing evidence / unsupported / unapproved item
   with what closes it.
6. **Machine-readable** — the package JSON (`template_sections`, `items`, `summary`,
   `readiness`) keyed by `request_id`.
7. **Standing note** — "Draft response package only; not submitted to any regulator, no exam
   item closed, and no system of record updated."
See [references/controls.md](references/controls.md).

## Privacy and records
**Restricted — AML/BSA.** SAR-confidentiality and tipping-off controls apply: never expose SAR
existence or subject-level detail to unauthorized parties, and never draft customer-facing text
revealing monitoring or SAR activity. Provide aggregate/desensitized figures to the examining
regulator under access control; mask customer/account identifiers to what the response requires.
Retain the package, citations, approver sign-offs, and template/config version per
recordkeeping obligations; log preparer identity and every read.

## Gotchas
- **Packaging ≠ submission.** Assembling and marking items ready is not sending the response;
  submission is a separate human act and is screened out of this skill.
- **A ready item is fully sourced and fully approved.** Either an unsourced assertion or a
  missing required approval keeps an item out of `draft-ready-for-review`.
- **Gaps are surfaced, never filled.** An unanswered request stays a `gap`; the skill will not
  invent a narrative or evidence to clear it.
- **Report issue/MRA status; do not close it.** Naming a remediation status is fine; resolving
  or closing the finding is the human's decision.
- **Template sections are a versioned contract.** Do not rename or drop a section; add
  jurisdiction detail inside a section and record the template/config version.
