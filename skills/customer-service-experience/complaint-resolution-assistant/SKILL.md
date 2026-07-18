---
name: complaint-resolution-assistant
description: >-
  Draft a controlled complaint-resolution package: classify the complaint, reconstruct a
  cited chronology, identify the applicable standards and root cause, compute a documented
  PROPOSED remediation (refund + interest + distress-and-inconvenience band + capped
  goodwill), and assemble a DRAFT final-response letter from the approved template. Use when
  a complaints handler or conduct-risk team member needs to work a complaint, quantify fair
  redress, or produce a first-draft response for review. HARD BOUNDARY: draft-only — it
  never sends or submits the response, never executes a payment, refund, or account change,
  never files a regulatory complaints return, and never makes the binding uphold/reject or
  liability decision. The proposed outcome and every figure are recommendations that a
  complaints handler and approver must review; external delivery and any system-of-record
  change route to the human owner or to omnichannel-case-orchestrator under approval.
license: MIT
compatibility: Amazon Quick Desktop; requires complaint-management/case-management, CRM, contact-center transcript, approved-knowledge/product-terms, and approved-calculation MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Complaints handler / conduct-risk team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Complaint Resolution Assistant

## Purpose and outcome
Turn a raw complaint record into a review-ready **draft resolution package**: a classified,
prioritized complaint; a cited chronology; the applicable standards and identified root
cause; a documented **proposed** remediation; and a DRAFT final-response letter built from
the approved template. The outcome is a complete first draft that a complaints handler and
approver can review, adjust, decide on, and (separately) deliver — it accelerates fair,
consistent complaint handling without ever making the decision or contacting the customer.

## Use when
- "Work this complaint / draft a response to this complaint."
- "Classify this complaint and reconstruct what happened."
- "What redress should we propose here?" (documented proposal, not a decision).
- "Which standards apply and what is the likely root cause?"
- "Prepare a draft final response for the handler to review."

## Do not use
- **Sending, submitting, or closing** the complaint, or executing a refund/payment/account
  change → human owner; execution routes to `omnichannel-case-orchestrator` (approval-gated).
- **Making the binding uphold/reject or liability decision** → complaints handler / approver.
- **Regulatory complaints reporting** (e.g., a periodic complaints return) → complaints /
  compliance team; this skill only flags that a report may be required.
- **Vulnerability assessment / accommodations** beyond flagging →
  `vulnerable-customer-support-assistant`.
- **General service-failure goodwill without a logged complaint** → `service-recovery-assistant`.
- **Personalized legal/financial advice**, or telling the customer to pursue litigation → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill drafts; it does not decide or
deliver. It consumes interaction summaries upstream and emits a durable `complaint_id`-keyed
draft package that a human (or, for execution, `omnichannel-case-orchestrator` under approval)
acts on. Duplicate execution is prevented by keeping decision, delivery, and reporting out of
scope.

## Inputs and prerequisites
- The complaint record: `complaint_id`, product, category, channel, received/resolution
  dates, `regulatory_reportable`, masked customer (with `vulnerability_flag`), the timeline
  `events[]`, documented `financial_loss_items[]` (amount + `loss_date` + `source_ref`), the
  `firm_error` determination (may be unknown), `root_cause_code`, `di_severity`, optional
  `amount_claimed` and `goodwill_requested`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The versioned **redress config** (interest rate, D&I bands, goodwill cap), **category
  severity**, **standards map**, and **root-cause map** (versioned contracts).
- Read access to complaint/case management, CRM, contact-center transcripts, and approved
  knowledge / product terms.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Complaint/case management is the
system of record for the complaint and its state; CRM and transcripts evidence the
interaction; approved knowledge and product terms establish the applicable standards. Cite
every evidence item; redress config and standards/root-cause maps are versioned contracts.

## Workflow
1. **Validate & normalize** — run `validate_input`; surface data gaps that force
   `needs-data`/`needs-review` rather than guessing.
2. **Classify & prioritize (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): category severity
   + vulnerability + regulatory-reportable + financial impact → a documented severity band.
3. **Reconstruct chronology** — order the `events[]` by date, each carrying a citation; never
   invent events to fill gaps.
4. **Map standards & root cause** — look up the applicable standards for the category and the
   root-cause summary from the versioned maps; unknown category → `needs-data`.
5. **Compute proposed remediation (deterministic)** — documented loss + simple interest
   (per item, loss_date → resolution_date) + the D&I band + goodwill capped at the config
   cap. Redress applies only where a firm error is documented; goodwill is discretionary.
6. **Draft the response** — assemble the DRAFT letter from [assets/output-template.md](assets/output-template.md)
   with all required sections, the DRAFT marker, and the proposed (not final) outcome.
7. **Record required approvals** — emit the approvals block (handler review + final approver)
   as pending; route vulnerability/reportable/execution items to the right owner.
8. **Never send/decide** — no delivery, payment, closure, filing, or binding decision.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: allowed dispositions/outcomes only; every required template
section + DRAFT marker present; required approvals recorded; remediation ties out and goodwill
is within cap; no unsupported/unapproved claims (liability admission, guarantee, promise,
legal advice, executed-payment language); no send/submit/file/close language; standing note
present. Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces a draft only. A complaints handler makes the
uphold/reject decision and an approver signs off before **any** external delivery or
system-of-record change; the approvals block records both. Internal drafting may be
reviewer-sampled, but the customer is never contacted and no redress is paid from here.

## Failure handling
- **Unknown category / no standards mapping** → `needs-data`; name the missing map entry.
- **Incomplete loss line or missing resolution_date** → `needs-data`; do not estimate redress.
- **`firm_error` undetermined** → `needs-review`; propose no outcome (investigation required).
- **Vulnerability indicator** → still draft, but set `refer-specialist` and route for
  accommodation review before finalizing.
- **Conflicting/stale sources** → cite both, flag, and do not resolve silently.
- **Tool timeout** → return the partial package with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Per-complaint record** — `complaint_id`, classification (category, severity band, root
   cause), cited chronology, applicable standards, proposed remediation breakdown + total,
   `proposed_outcome` (`uphold` | `partial-uphold` | `not-upheld` | `needs-review`),
   `disposition` (`draft-ready` | `refer-specialist` | `needs-data` | `needs-review`).
2. **Draft response letter** — assembled from the template, marked DRAFT, all required
   sections present, outcome labeled proposed/pending approval.
3. **Approvals block** — handler review + final approver (recorded, pending).
4. **Routing notes** — vulnerability, regulatory-reportable, and execution handoffs.
5. **Machine-readable** — the package keyed by `complaint_id`.
6. **Standing note** — "Draft complaint response only … Nothing has been sent to the customer
   or reported to a regulator."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (customer NPI/PII).** Mask customer identifiers to what evidences the
complaint. Draft outputs contain PII: restrict to the handling team, retain with the
complaint record and the config/standards versions used, and log the drafter identity. No
customer contact, payment, or regulatory submission originates here.

## Gotchas
- **Draft ≠ decision ≠ delivery.** The proposed outcome is a recommendation; a human decides
  and a human (or the orchestrator under approval) delivers.
- **Redress needs a documented error.** Interest and refund apply only where `firm_error` is
  true and the loss line is complete; goodwill is discretionary and capped.
- **Never admit legal liability or promise a guaranteed result.** Explain findings against
  standards; the output validator blocks liability/guarantee/legal-advice language.
- **Tipping the outcome without evidence is a fail.** Unknown category or undetermined error
  routes to `needs-data`/`needs-review`, not a manufactured answer.
- **Vulnerability is a routing signal, not a diagnosis.** Flag and refer; do not conclude a
  condition.
- **Config is a versioned contract.** Record the redress/standards/root-cause versions so a
  proposal is reproducible and reviewable.
