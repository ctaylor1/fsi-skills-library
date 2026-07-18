---
name: next-best-action-assistant
description: >-
  Draft a ranked, source-cited next-best-action package for a service agent or relationship
  manager from customer context (CRM, contact-center transcript, case, complaint status) using
  an APPROVED action catalog. Recommends only policy-compliant service, education, referral, and
  retention actions, each gated by product/tenure/signal eligibility, marketing consent and
  do-not-contact, and a vulnerability flag, and each carrying citations and required disclosures.
  Use when an agent asks "what should I offer or do next for this customer", wants compliant
  retention or education options, or needs referral suggestions from the interaction context.
  HARD BOUNDARY: draft-only — it never sends, submits, or writes a system of record, and it never
  makes or communicates a binding credit, claim, or investment/suitability decision or gives
  personalized investment advice; those are excluded and routed to a licensed specialist.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, contact-center transcript, case-management, complaint-system, approved-knowledge, and product-terms MCP integrations (all read-only), plus the approved action-catalog/eligibility-rules config.
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
  aws-fsi-primary-user: "Service agent / relationship manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Next-Best-Action Assistant

## Purpose and outcome
Turn a customer's context into a **draft** next-best-action package an agent can act on: a
ranked list of policy-compliant service, education, referral, and retention actions drawn from
the **approved action catalog**, each one eligibility-checked, consent-aware, cited, and paired
with its required disclosures. The outcome is a review-ready package — the agent (with the
required approvals) decides what to offer and delivers it. Binding decisions and licensed advice
are deliberately out of scope and routed onward.

## Use when
- "What are the next best actions for this customer?" / "What should I offer next?"
- "Give me compliant retention or education options for this account."
- "Any referral suggestions based on this call?"
- "Rank the things I could do for this customer and tell me why."

## Do not use
- **Binding credit decisions** (approve/decline, limit increase, adverse action) → refer to
  `loan-affordability-precheck` / `credit-application-packager` and a licensed lending specialist.
- **Investment advice / suitability** ("how should they reallocate?") → `suitability-reg-bi-reviewer`
  and a licensed adviser; older-investor concerns → `senior-investor-protection-screener`.
- **Claim coverage/denial decisions** → a licensed claims specialist.
- **Complaint handling** → `complaint-resolution-assistant`; **service failure remediation** →
  `service-recovery-assistant`.
- **Delivering** any recommendation (send/submit/post) → not here; draft-only.
- Any request to guarantee an outcome, mark a customer "pre-approved", or recommend an action
  not in the approved catalog → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream context comes from
`customer-interaction-summarizer`, `omnichannel-case-orchestrator`, and `knowledge-answer-composer`.
Prohibited/binding items are routed once (recorded in `specialist_referrals`), never re-attempted
as recommendations. Where no catalog skill fits (the actual credit/claims/suitability decision),
the handoff is to a **licensed human specialist**, not an automated skill.

## Inputs and prerequisites
- Customer context: `customer_ref`, segment, products held, tenure, **consent** (per channel),
  **do-not-contact**, **vulnerability flag**, open-complaint status, and context signals from the
  interaction; plus `context_refs` (CRM/transcript/case). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **approved action catalog** + eligibility rules (`config_version`): the allow-list of
  recommendable actions with eligibility, consent/specialist metadata, disclosures, and source refs.
- Read access to CRM, transcripts, case management, complaint system, approved knowledge, and
  product terms.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The action catalog is the highest
authority and the **allow-list**; approved knowledge and product terms supply citations and
disclosure text; CRM/transcript/case/complaint supply customer context. Catalog, knowledge, and
terms are **versioned/effective-dated contracts**. Cite every recommendation.

## Workflow
1. **Validate & load** — run `validate_input`; load the customer context and the approved catalog
   at its `config_version`. Read consent, do-not-contact, and vulnerability flags **fresh**.
2. **Complaint short-circuit** — if the interaction is a complaint, route to
   `complaint-resolution-assistant` rather than drafting offers.
3. **Evaluate the catalog (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). For each catalog action:
   (a) exclude+route any **binding** decision (credit/claim/investment/suitability); (b) check
   **eligibility** (product/tenure/signal/segment); (c) **suppress** retention/cross-sell for a
   vulnerable customer and route to specialist support; (d) apply **consent/do-not-contact**
   gating for outbound actions; (e) otherwise recommend, with citations and disclosures.
4. **Rank** — order eligible actions by the documented score (benefit + matched signals); this
   ranks a human's options, it is not an approval.
5. **Assemble the draft package** — fill [assets/output-template.md](assets/output-template.md):
   context snapshot, ranked recommendations, consent/eligibility checks, excluded/routed items,
   aggregated disclosures, recorded (pending) approvals, sources, standing note.
6. **Never deliver** — no sending, submitting, posting, or system-of-record write.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; every recommendation cited and
non-binding; no guarantee/advice/approval claim language; no send/submit/executed language
(draft-only); approvals recorded and `external_delivery` not true without an `approved` status;
standing note present. Fail closed on any miss and fix before presenting.

## Human approval
`external-delivery`. A servicing supervisor / QA reviewer must approve before any recommendation
is delivered externally or written to a system of record; a referral is acted on only after
licensed-specialist sign-off. Internal drafting is reviewer-sampled. The package proposes; humans
approve and deliver.

## Failure handling
- **Missing/invalid context** (no risk-relevant fields, empty catalog) → `validate_input` errors;
  stop and surface exactly what is missing. Do not invent context.
- **Missing signal / consent unknown** → the action is excluded (ineligible / consent-gated) with
  a reason; never assume consent to enable an outbound action.
- **Vulnerability flag present** → suppress retention/cross-sell; route to
  `vulnerable-customer-support-assistant`.
- **Prohibited/binding request** → refuse to recommend; record a specialist referral instead.
- **Stale catalog/terms/consent** → cite the version; if a consent read is stale, treat outbound
  as not permitted (fail closed).
- **Tool timeout / partial context** → return the partial package with an explicit incomplete flag;
  assume no retry or step-up.

## Output contract
1. **Draft package** (`nba-package-v1`) with sections: Customer Context Snapshot; Recommended Next
   Best Actions (ranked; each with action_id, type, rationale, eligibility basis, citations,
   required disclosures, specialist flag); Consent & Eligibility Checks; Excluded or Routed to
   Specialist (with reasons); Required Disclosures; Approvals & Handling; Sources.
2. **Machine-readable** — `recommendations[]`, `excluded[]`, `specialist_referrals[]`, `approvals{}`
   (status `pending`, `external_delivery: false`), keyed to `customer_ref` and `config_version`.
3. **Standing note** — "Draft recommendations only. No action here is a binding credit, claims, or
   investment decision; nothing has been delivered to the customer or written to any system of
   record."
See [references/controls.md](references/controls.md) and [references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential (customer NPI/PII).** Mask customer/account identifiers to what the package
needs; keep raw PII out of rationale text. Honor consent, do-not-contact, and vulnerability flags
on every package. Retain the draft package, `config_version`, citations, and recorded approvals;
log the agent identity on every read and every package produced.

## Gotchas
- **The catalog is the allow-list.** If an action is not in the approved catalog (or has no
  citation), it cannot be recommended — no improvising a helpful-sounding offer.
- **Referral ≠ decision.** Recommending "refer to a licensed mortgage specialist" is fine;
  approving credit, quoting a guaranteed rate, or advising an allocation is not.
- **Consent is per-channel and fail-closed.** No matching channel consent (or do-not-contact set)
  means the outbound action is excluded, not "flagged for later".
- **Vulnerability suppresses sales pressure.** Retention/cross-sell is withheld and routed, even if
  otherwise eligible.
- **Draft-only means draft-only.** The package never sends, submits, posts, or updates a record;
  external delivery is a separate, approved, entitled step.
- **Ranking is not approval.** A rank-1 action is still a proposal a human must approve.
