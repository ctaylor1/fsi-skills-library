---
name: insurance-rate-form-filing-packager
description: "Assemble a rate/form/rule regulatory filing packet from its components and deterministically test completeness against the approved filing checklist, rate-change support, required exhibits, and effective-date/notice rules; produce a source-linked gap-evidence packet for a human product-filing analyst and compliance reviewer. Use when a filing analyst asks to \"package this SERFF filing\", \"check the filing is complete before submission\", \"what's missing from this rate filing\", or \"cross-check the exhibits\". HARD BOUNDARY: R3 draft/decision-support only — it NEVER submits or files anything with a regulator, never certifies a filing as compliant or approvable, and never sets or approves a rate; every disposition is a recommendation an authorized human must adjudicate. Routes bounded prospective P&C rate-support work to pc-rate-adequacy-analyzer for qualified pricing-actuary review."
license: MIT
compatibility: Python 3.10+; offline structured inputs and supplied source evidence. Expected source systems are not bundled production connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 1"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Insurance product and filing compliance"
  aws-fsi-primary-user: "Product filing analyst"
  aws-fsi-version: "0.2.1"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Rate and Form Filing Package

## Implemented scope and evidence contract

This is a rate/form/rule completeness and supplied-checklist review, not regulatory reporting generally or rate-adequacy analysis. `checks_run` contains evaluated checks only; unevaluable checks force `incomplete`. Presence references do not establish substantive exhibit correctness or legal applicability. Bounded prospective P&C indications belong to `pc-rate-adequacy-analyzer`; a qualified pricing actuary selects assumptions and approves actuarial support.

All output artifacts include the portable insurance evidence contract and source snapshot. Missing actor, versioned source, date or upstream context remains explicitly partial. Content hashes detect changes; they do not authenticate sources or grant approval. After authoring narrative, rebuild `artifact` with `build_artifact` from `scripts/insurance_contract.py` before running output validation. A common envelope does not replace the receiver's native input validator.

## Purpose and outcome
Given the components of a rate/form/rule filing, deterministically test them against the
approved filing checklist (required components, required exhibits), rate-change support, and
effective-date/notice rules; surface every gap with cited evidence and a suggested review
disposition. A successful output lets a product-filing analyst and compliance reviewer decide —
the submission and any compliance judgment remain the human's.

## Use when
- "Package/assemble this filing", "check the filing is complete before submission".
- "What's missing from this rate/form/rule filing", "cross-check exhibits against the checklist".
- A reviewer needs a consistent, cited filing-gap packet.

## Do not use
- The user wants you to **submit or file** with a regulator → out of scope; the human/filing
  system acts.
- The question is about **rate adequacy / actuarial support** itself → route to
  `pc-rate-adequacy-analyzer` for its supported supplied-assumption P&C method, with qualified pricing-actuary review; broader methods require a specialist.
- Policy-wording comparison across form versions → `policy-wording-comparator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a gap-evidence packet with a durable
`packet_id`; it does not submit, approve, or set rates.

## Inputs and prerequisites
- The **filing**: id, type (rate|form|rule), state, company, effective_date, as_of,
  proposed_rate_change_pct; the **checklist** (required components/exhibits, notice rule,
  version); and **components[]** / **exhibits[]** with present flags and source refs. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Approved **filing-checklist config** — a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Filing-management record is the system
of record; exhibits from actuarial; checklist from versioned config. Cite every gap to a source
line + checklist rule/version.

## Workflow
1. **Validate input** — run `validate_input`; confirm one filing, its type, and required fields.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): completeness vs
   required components, required-exhibit presence, rate-change support (filed vs indicated
   within tolerance or a justification component present), and effective-date/notice lead.
3. **Assemble gaps** — per gap: rule, expected vs found, evidence line, checklist version.
4. **Suggest disposition** — `ready-for-review` or `gaps-for-review` (a triage suggestion, not
   a submission or compliance decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-submit/no-certify screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a gap lacks a citation, or the text
contains submission/approval/certification language, **fix or fail closed**.

## Human approval
`required`: no submission, rate approval, or compliance certification without an authorized
human. The skill only evidences gaps.

## Failure handling
- **Missing checklist/config** → fail closed; state what is missing; do not assume a checklist.
- **Filed rate exceeds indicated** with no justification component → flag as a gap; never
  rationalize it.
- **Missing exhibit** → flag, do not fabricate a value.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — filing (masked), type, checklist version, count of gaps, suggested disposition.
2. **Gaps** — per gap: rule, expected vs found, citation.
3. **Data gaps / not-evaluable checks.**
4. **Machine-readable** — checks + gaps + `packet_id`.
5. **Standing disclaimer** — "Filing-gap evidence only; not a filing submission or a compliance
   certification. No filing has been submitted and no rate has been approved."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy/insured identifiers. Retain the packet + citations + checklist
version. Log read + external-delivery approval. Never exfiltrate filing data.

## Gotchas
- **A gap is not a rejection.** Flag it; the analyst/regulator decides.
- **Rate support**: "filed = indicated" is not required, but a filed rate above indicated needs
  a documented justification component — report its absence factually.
- **Effective date**: an effective date inside the required notice window is a gap, not a
  decision to delay.
- **"Missing exhibit" ≠ "non-compliant"**: report the missing item; the reviewer determines
  significance.

## Evidence and handoff contract

Read [the insurance evidence contract](references/insurance-contract.md) for source
versioning, explicit unknowns, financial/date bases and receiver validation. A
content hash is not source authentication, professional approval or execution authority.
