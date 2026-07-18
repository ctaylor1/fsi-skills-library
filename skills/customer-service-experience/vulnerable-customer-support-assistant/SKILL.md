---
name: vulnerable-customer-support-assistant
description: >-
  Identify possible support needs from customer-provided context in a service interaction, map
  each need to an approved-catalog accommodation and, where warranted, a specialist or
  safeguarding referral, and draft a review-ready support-needs assessment for a service agent
  or vulnerability specialist. Use when an agent asks to "flag support needs", "what
  accommodations can I offer this customer", "should this go to the vulnerability or
  safeguarding team", or needs a cited draft built from a call transcript, chat, or CRM note.
  This skill is drafting support only: it NEVER diagnoses a medical, mental-health, or cognitive
  condition, NEVER makes a discriminatory or mental-capacity determination or limits service on
  a protected characteristic, NEVER gives financial, medical, or legal advice, and NEVER applies
  a vulnerability marker or accommodation to any system of record or sends anything to the
  customer — a human reviews and an authorized colleague acts.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, contact-center transcript, case-management, approved-knowledge, product-terms, and complaint-system MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Service agent / vulnerability specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Vulnerable Customer Support Assistant

## Purpose and outcome
Given the **customer-provided context** of a service interaction — a call transcript, chat,
complaint text, or CRM note — surface the **possible support needs** the customer has actually
signalled, map each to an **approved accommodation** and, where the signals warrant it, a
**specialist or safeguarding referral**, and assemble a cited, review-ready **support-needs
assessment (draft)**. A successful output lets an agent respond with empathy and offer the
right, pre-approved accommodations — after a human confirms them. The skill never labels the
customer, never decides their capacity, and never writes anything to a system of record or to
the customer. It drafts; a human reviews and an authorized colleague acts.

## Use when
- "Flag any support needs from this call and suggest what we can offer."
- "What accommodations can I offer this customer based on what they told me?"
- "Should this interaction go to the vulnerability or safeguarding team?"
- "Draft a support-needs note for the CRM from this chat transcript."
- An agent needs a consistent, cited support-needs work-product to attach to a case.

## Do not use
- The user wants a **diagnosis** or a clinical opinion ("does this customer have dementia?")
  → out of scope; this skill never diagnoses. Refer welfare questions to trained specialists.
- The user wants a **mental-capacity or fitness determination**, or to **deny/limit service**
  based on a condition or protected characteristic → prohibited; escalate to the vulnerability
  specialist and compliance.
- The user wants **financial, investment, medical, or legal advice** → out of scope; signpost
  to the appropriate licensed professional or approved support organization.
- The interaction is primarily a **complaint to resolve** → `complaint-resolution-assistant`.
- The user just wants the interaction **summarized** → `customer-interaction-summarizer`.
- The user wants the **next approved offer/action** turned into a customer response →
  `next-best-action-assistant` (consumes this draft; does not replace the review gate).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a support-needs
assessment with a durable `assessment_id`; a human reviews it and an authorized colleague
applies any marker or accommodation and makes any referral. Upstream context typically comes
from `customer-interaction-summarizer` or `omnichannel-case-orchestrator`; downstream, approved
accommodations may be offered via `next-best-action-assistant` or `service-recovery-assistant`.
Referral to a vulnerability specialist or safeguarding team is a **human/operations** action,
not a skill.

## Inputs and prerequisites
- The **interaction record**: `customer_ref` (masked), channel, and the **observed signals** —
  each a short quote the customer actually said/wrote, with a `source_ref` into the transcript
  or note. The skill does not infer a need without a cited cue.
- The **consent context**: whether special-category data is involved and the customer's consent
  status for recording it and arranging accommodations.
- The **versioned config**: approved vulnerability-drivers taxonomy, signal → driver map,
  approved accommodations catalog, and approved referral routes
  (see [references/domain-rules.md](references/domain-rules.md)). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to CRM, contact-center transcripts, case management, approved knowledge, product
  terms, and the complaint system (all read-only).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **customer's own words** in the
interaction are the only basis for a support need — cite each signal to its transcript line.
The approved **drivers taxonomy, accommodations catalog, and referral routes** are versioned
contracts; the CRM is the system of record but this skill only reads it. If a colleague's prior
note conflicts with what the customer says now, cite both and flag — never resolve silently.

## Workflow
1. **Scope & validate** — load the interaction and config; run `validate_input`. Fail closed on
   structural gaps; note data-quality warnings (unmasked ids, signals without a `source_ref`,
   special-category data without a consent status).
2. **Map signals (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): for each cited signal
   it assigns a **driver category** (Health, Life events, Resilience, Capability), selects the
   **approved accommodations** whose applicability matches that signal type, chooses a
   **suggested referral route** by the documented priority (safeguarding first), and records
   consent and approval flags. Every accommodation traces to at least one cited signal.
3. **Assemble the draft** — restate each signal neutrally, list the possible support needs,
   the suggested (approved-only) accommodations, and the suggested referral, following
   [assets/output-template.md](assets/output-template.md). Mark it `human_review_required`.
4. **Never label, never apply** — do not conclude the customer *is* vulnerable, *has* a
   condition, or *lacks* capacity; do not apply a marker or accommodation to the CRM; do not
   send anything to the customer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: every suggested accommodation is in the approved catalog and is
traced to a cited signal (no unsupported/unapproved claims); the referral route is approved; the
required template sections are present; no diagnostic, discriminatory / capacity-determination,
or advice language is present; the record update is `proposed` and not applied; the draft is
marked `human_review_required`; and the standing note is present. Fail closed on any miss.

## Human approval
`external-delivery`. Human review is required before the assessment is shared beyond the agent,
before any vulnerability marker or accommodation is recorded in the CRM, and before any referral
is made. No approval is needed for the reviewing agent's own read. The skill never writes to a
system of record and never contacts the customer.

## Failure handling
- **No cited signals** → return an assessment stating no support need was identified from the
  provided context; suggest nothing. Do not infer vulnerability to be safe.
- **Signal without a `source_ref`** → treat as data-quality gap; do not build a suggestion on an
  uncited claim.
- **Special-category data without consent** → still draft, but mark consent-dependent
  accommodations `pending_consent` and list capturing consent as a required next step.
- **Heightened-risk signal** (disclosed abuse or risk of harm) → force the safeguarding referral
  route and a prominent, time-sensitive human-review flag; never diagnose or delay behind the
  draft.
- **Ambiguous customer identity** → stop and confirm; never attach the draft to the wrong record.
- **Tool timeout** → return the signals mapped so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — `customer_ref` (masked), channel, count of signals, suggested referral,
   readiness, `assessment_id`.
2. **Observed signals** — each cited to its transcript line, with its driver category.
3. **Possible support needs** — the driver categories evidenced, framed as possibilities.
4. **Suggested accommodations** — approved-catalog items only, each traced to its signal(s),
   with any `pending_consent` flag.
5. **Suggested referral** — an approved route (safeguarding / specialist / financial-difficulty
   / external-support signpost) with the reason and supporting signals.
6. **Consent and approvals** — consent status and the recorded human-review / no-record-change
   flags.
7. **Machine-readable** — the assessment work-product + `assessment_id` for reuse.
8. **Standing note** — the verbatim "draft only; not a diagnosis; nothing applied or sent" note.
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (customer NPI/PII), including special-category data.** Mask
customer identifiers to the last 4. Minimize sensitive detail to the cited signal that
evidences a need. Record special-category data only with a captured consent status. Retain the
assessment work-product + citations + config version per records policy; log the read and the
external-delivery / record-change approvals. Never exfiltrate customer or health data.

## Gotchas
- **A signal is not a diagnosis.** "I've been feeling low since my husband died" is a *life
  event and possible health signal* to support — never a diagnosis of depression. Diagnostic
  language is prohibited and screened.
- **Support is not a determination.** Never conclude the customer *is* vulnerable, *lacks
  capacity*, or cannot manage their money — those are labels/legal determinations this skill
  must not make, and they can be discriminatory.
- **Approved catalog only.** If an accommodation is not in the approved catalog, it is not
  suggested; the template and `validate_output` both enforce this.
- **No suggestion without a cited cue.** Missing evidence is silence, not an inference. The
  skill fails closed to "no support need identified" rather than guessing.
- **Vulnerability can be transient.** A support need tied to a life event may be temporary;
  frame it as current context, and let the human and customer decide what to record.
- **Draft, don't do.** The skill never records a marker, applies an accommodation, or messages
  the customer — a human reviews and an authorized colleague acts.
