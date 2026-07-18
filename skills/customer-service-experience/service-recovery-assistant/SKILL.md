---
name: service-recovery-assistant
description: >-
  Assess a customer service failure and draft a remediation-and-communication package for
  human approval: score severity and customer impact, weigh precedent, policy, and
  fair-value, then compute a proposed remediation (documented direct redress plus a goodwill
  gesture bounded by the approved matrix) and draft an apology in approved language. Use when
  a service agent, complaints handler, or CX/operations user must put right a service failure
  (delayed payment, incorrect fee, outage, missed callback, misinformation) and wants a
  consistent, cited draft with the approval tier. HARD BOUNDARY: draft-only — it
  never sends a communication, never pays/credits/posts goodwill or redress, never proposes
  goodwill above the matrix cap or redress of an undocumented detriment, never admits legal
  liability, guarantees an outcome, or gives investment/legal/tax advice, and never decides a
  formal regulated complaint (route to complaint-resolution-assistant). External delivery and
  payment require the recorded human approval.
license: MIT
compatibility: Amazon Quick Desktop; requires case/complaint-management, CRM, contact-center-transcript, approved-knowledge/product-terms, and approved-calculation (goodwill/redress matrix) MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Customer Service & Experience"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Customer Service & Experience"
  aws-fsi-primary-user: "Customer-experience / complaints / operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Service Recovery Assistant

## Purpose and outcome
Turn a customer **service failure** into an approval-ready recovery package. For each case
the skill assesses what went wrong and its impact, weighs precedent, policy, and fair-value
considerations, computes a **proposed remediation** (documented direct redress plus a
goodwill gesture bounded by an approved, versioned matrix), and drafts a customer
communication in approved language whose only figures are the computed ones. The outcome is
a consistent, cited draft with the **required approval tier recorded** — ready for a human
to approve, and for authorized operations to deliver. Nothing is sent or paid by this skill.

## Use when
- "We let this customer down — draft a service-recovery response and a fair goodwill gesture."
- "Work out an appropriate remediation for this outage / incorrect fee / missed callback and
  package it for a manager to approve."
- "Assess this service failure, check precedent and policy, and draft the apology."

## Do not use
- **Formal / regulated complaint** handling or a final-response decision → refer to
  `complaint-resolution-assistant`.
- **Vulnerability** assessment and accommodations → `vulnerable-customer-support-assistant`.
- **Sending** the communication or **paying/posting** the remediation → not this skill;
  after approval, delivery/coordination is `omnichannel-case-orchestrator` + the approval
  broker.
- Any request to **admit liability**, **guarantee** an outcome, quote an **unsupported
  figure**, exceed the **matrix cap**, or give **investment/legal/tax advice** → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Recovery drafting is separate from
complaint adjudication, vulnerability support, and execution (delivery/payment). This skill
emits a durable `case_id` + draft package; it must not perform the approver's or the
executor's work.

## Inputs and prerequisites
- The service-failure case(s) with `case_id`, customer id, failure type, dates, and source
  refs; contact-center commitments; customer profile (tenure, vulnerability flag); the
  documented financial detriment (if any) and whether it is substantiated; applicable
  policy/product-term refs; the versioned **goodwill/redress matrix** and **approval
  thresholds**; a precedent set. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to case/complaint management, CRM, transcripts, approved knowledge/terms, and
  the approved-calculation config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case management is the system of
record for the failure and remediation state; CRM for the customer; transcripts for what was
promised; approved knowledge/terms for the explanation. The matrix, thresholds, and approved
apology language are **versioned contracts**. Cite every finding, figure, and claim.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm required fields; surface data
   gaps (undocumented detriment, unknown distress, no policy grounding) as warnings.
2. **Route out early** — a `formal_complaint` case is `refer-specialist` to
   `complaint-resolution-assistant` (not drafted here); a vulnerability flag adds a
   `vulnerable-customer-support-assistant` referral and forces Tier 3 approval.
3. **Score (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes severity
   and customer-impact bands from documented inputs (explainable, not a black box).
4. **Compute remediation** — goodwill gesture from the matrix (`severity`×`impact`, capped);
   direct redress only for a **documented** detriment (else `needs-data`, no redress);
   `total = redress + goodwill`; derive the approval tier.
5. **Draft the package** — assemble the sections in
   [assets/output-template.md](assets/output-template.md): failure assessment, impact,
   precedent/policy + fair-value note, proposed remediation, and a customer communication in
   approved language whose figures are only the computed values, all cited.
6. **Record required approval** — set the tier + approver role, status `pending`. Never set
   `sent`, `paid`, or `closed`; `delivery.sent` stays false.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. Output check enforces: draft-only dispositions (no send/pay/close); every draft has
all required template sections, cited; remediation ties out and stays within the matrix cap;
every quoted figure is a computed value; the required approval is recorded (tier + role; a
`recorded` status needs a named approver + decision); no liability/guarantee/entitlement/
advice/"already actioned" language; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. A recorded human approval at the computed authority tier
(agent ≤ $50, team lead ≤ $150, manager otherwise / vulnerability / above authority) is
required before the communication is delivered or any goodwill/redress is paid or posted.
This skill proposes and packages; humans approve and execute. See
[references/controls.md](references/controls.md).

## Failure handling
- **Undocumented detriment** → `needs-data`; propose no redress and list the evidence
  needed; never invent or estimate a reimbursement.
- **Missing impact inputs** (unknown distress) → `needs-data`; do not guess a band.
- **Formal complaint** → `refer-specialist` to `complaint-resolution-assistant`.
- **Above-matrix warranted** → do not draft a figure over the cap; escalate as a manager
  exception.
- **Stale/conflicting sources** → cite both and flag for review; do not draft over a
  conflict.
- **Tool timeout** → return the partial package with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Package** (per case) — `case_id`, masked `customer_ref`, disposition
   (`draft-for-approval` | `needs-data` | `refer-specialist`), and for drafts the full
   section set from the template (assessment, impact, precedent/policy, proposed
   remediation, communication, required approvals, sources).
2. **Proposed remediation** — direct redress + goodwill = total, reason codes,
   `matrix_version`, cap check, citations.
3. **Draft communication** — apology, explanation, remediation offer, next steps; approved
   language; computed figures only; cited.
4. **Required approvals** — tier + approver role, status `pending`.
5. **Machine-readable** — the package records keyed by `case_id`, with a `delivery.sent:
   false` flag.
6. **Standing note** — "Draft for human review only; no communication has been sent and no
   goodwill or redress has been paid."
See [references/domain-rules.md](references/domain-rules.md) for the scoring, matrix, and
tiers.

## Privacy and records
**Highly Confidential (customer NPI/PII).** Mask customer identifiers to what evidences the
case (`customer_ref` masked to the last 4). Retain the draft package, the computed
remediation with `matrix_version`, citations, and the approval record per complaint/records
retention; log the drafter identity and every read. Do not place customer data in
communications to any recipient not on the case.

## Gotchas
- **Goodwill ≠ redress.** Goodwill is a bounded gesture from the matrix; redress reimburses
  a *documented* detriment. Never fund redress from an unsubstantiated amount.
- **Draft ≠ done.** The communication is phrased as an offer *subject to approval*; the skill
  never sends, credits, or pays, and never writes "we have credited/refunded".
- **No liability, no guarantees.** Apologize and put it right in approved language; do not
  admit fault/negligence, promise it "will never happen again", or assert entitlement.
- **Figures are computed, not invented.** Any amount quoted to the customer must equal the
  redress, goodwill, or total the engine produced.
- **The matrix and thresholds are versioned.** Record `matrix_version` on every remediation
  so the decision is reproducible and reviewable.
- **Vulnerability and formal complaints leave this lane.** Route them; do not absorb the
  specialist's or the complaint decision-maker's job into a recovery draft.
