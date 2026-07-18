---
name: collections-treatment-planner
description: >-
  Recommend compliant, customer-appropriate collections outreach and treatment options for a
  delinquent account by combining delinquency context, vulnerability/hardship indicators,
  consent and suppression flags, contact-frequency limits, and versioned policy, then present
  an evidenced shortlist for a specialist to adjudicate. Use when a collections specialist or
  hardship-team member asks "what treatment options apply to this delinquent account", "what
  outreach is compliant here", "which hardship options is this customer eligible for", or
  needs a review-ready treatment plan. This skill recommends and evidences options and
  respects suppression/contact caps; it NEVER approves or denies a treatment, grants
  forbearance, modifies a loan, sets up an arrangement, agrees a settlement, re-ages, closes a
  case, charges off, files, or reports to a bureau — those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking, CRM, document-intelligence, loan-servicing, product-terms, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Collections specialist / hardship team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Collections Treatment Planner

## Purpose and outcome
Given a delinquent account's servicing context, contact history, consent/suppression flags,
and any vulnerability/hardship indicators, derive the **delinquency band**, run the
**suppression** and **contact-frequency** screens, flag **enhanced-care** handling, and map
the case to an evidenced shortlist of **eligible treatment options** with policy citations.
A successful output lets a collections/hardship specialist choose and offer an appropriate,
compliant treatment quickly — the **adjudication, the offer, and any system change remain
human/authorized-system actions**.

## Use when
- "What treatment options apply to this delinquent account?"
- "What outreach is compliant for this customer right now?"
- "Which hardship options is this customer eligible for?"
- A specialist needs a consistent, cited treatment shortlist to attach to a collections case.

## Do not use
- The user wants the skill to **make the decision** — approve/deny a treatment, grant
  forbearance, modify the loan, agree a settlement, re-age, close the case, charge off, file,
  or report to a bureau → out of scope. Recommend and route to the human/authorized system.
- **Staging and executing** an approved servicing change (due-date change, re-age, forbearance
  booking) → `loan-servicing-exception-resolver` (R4, after human approval).
- **Specialist accommodation / referral** for a vulnerable customer →
  `vulnerable-customer-support-assistant`.
- **Affordability sizing / substantiation** → `loan-affordability-precheck`,
  `bank-statement-analyzer`, or `cashflow-forecaster`.
- The customer **disputes the delinquency as an error** or raises a complaint →
  `complaint-resolution-assistant`.
- **Attorney-represented, litigation, bankruptcy, or SCRA** matters → flag the suppression and
  route to the licensed specialist / legal team (human handoff, not a skill).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a treatment-plan pack
with a durable `plan_id`; downstream support, affordability, and execution skills consume it.
It must not duplicate their adjudication, offer, or execution steps.

## Inputs and prerequisites
- Account identifier (masked) and **delinquency context**: product type, days-past-due,
  balance, minimum due, past-due amount, all as of a stated date.
- **Contact history** (date, channel, outcome) sufficient to apply the contact-frequency
  screen, and **suppression/consent flags** (cease-communication, attorney-represented,
  dispute-pending, do-not-contact window, bankruptcy, SCRA).
- Optional **vulnerability/hardship indicators** and **disclosed income/expenses** (indicative
  affordability only). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to servicing, CRM, and product terms; versioned policy config (bands,
  eligibility rules, contact caps) — see [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **servicing system of record** is
authoritative for delinquency figures; CRM is authoritative for consent/suppression flags and
disclosed context; product terms govern treatment specifics; policy config supplies bands,
eligibility rules, and caps. Cite every eligible treatment to its delinquency basis and policy
rule. Never substitute a verbal balance for the servicing record; honor suppression flags even
when other data invites outreach.

## Workflow
1. **Scope & validate** — confirm the account and `as_of`; load the case; run
   `validate_input`. Fail closed on missing identity or bad delinquency figures.
2. **Screen (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to derive the
   delinquency band, apply the **suppression** screen (halt outreach on any hard flag), apply
   the **contact-frequency** screen (Reg F 7-in-7 phone presumption), and flag **enhanced
   care** when any vulnerability indicator is present.
3. **Map eligibility** — for each configured treatment, evaluate its documented rule and attach
   eligibility evidence + a policy citation. Ineligible options are shown with the rule missed.
4. **Build the outreach plan** — recommend channels that honor the suppression screen and the
   call cap, with a supportive tone for enhanced-care cases and a next-review suggestion.
5. **Write the pack** — plain-language summary + the eligible shortlist (each cited) + the
   outreach recommendation + care prompts + the explicit human-adjudication requirement.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: `requires_human_adjudication` is true and the disclaimer is present;
every eligible treatment is cited; `recommended_treatments` ties out exactly to the eligible
set; no regulated-decision/closure/filing/reporting/commitment language and no threats are
present; suppression is honored (no eligible channel when suppressed); and the call cap is
honored (`phone` only when eligible). **Fail closed on any miss.**

## Human approval
`required`: a collections/hardship specialist must **adjudicate and authorize** before any
treatment is offered, any outreach is initiated, or any system of record is changed. The skill
performs read-only analysis and stages nothing for execution; executing an approved change is
`loan-servicing-exception-resolver` (R4). No approval is needed for the specialist's own read.

## Failure handling
- **Missing/bad delinquency figures or identity** → stop and confirm; never plan on the wrong
  account or a negative DPD.
- **No contact history** → the call-frequency screen is not evaluable; treat phone caps as
  unknown and require the human to confirm before any call.
- **No suppression block** → flags are assumed false; surface that assumption and require
  confirmation before outreach.
- **No disclosed income/expenses** → `payment_arrangement` sizing is not evaluable (indicative
  only); do not fabricate affordability.
- **Stale/conflicting sources** → cite both (servicing vs. CRM) and flag; do not resolve silently.
- **Tool timeout** → return the screens and eligibility computed so far with an "incomplete" flag.

## Output contract
1. **Summary** — account (masked), `as_of`, product, delinquency band, enhanced-care flag,
   suppression status, phone attempts remaining.
2. **Eligible treatments** — per eligible option: name, rationale, cited evidence (delinquency
   basis + policy rule), and `requires_human_review`. Ineligible options with the rule missed.
3. **Outreach plan** — eligible/suppressed channels, cadence note (within the call cap and
   quiet hours), and tone.
4. **Care prompts** — enhanced-care handling reminders when vulnerability is present.
5. **Machine-readable** — screens + eligible set + `plan_id` for downstream skills.
6. **Standing disclaimer** — "Recommendations and evidence only; every treatment option and
   outreach action requires human adjudication and authorization. No collections decision has
   been made, no case has been closed, and no system of record has been updated."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (last 4). Minimize customer data to what evidences an
eligibility decision. Retain the plan + citations + config version per records policy; log the
read and the specialist's adjudication/authorization. Never exfiltrate customer data.

## Gotchas
- **A shortlist is not a decision.** Eligible treatments are options for a specialist to weigh
  and offer, never an approval, an offer, or a booked arrangement.
- **Suppression flags win.** Cease-communication, attorney-represented, dispute-pending,
  do-not-contact, and bankruptcy halt outreach regardless of how "collectible" the account
  looks; the plan must show zero eligible channels when suppressed.
- **Contact caps are a compliance line.** The 7-in-7 phone presumption is enforced from the
  contact history; do not recommend a call that would breach it, and surface quiet hours.
- **Hardship is a care input, not an adverse one.** Enhanced care prefers forbearance /
  affordability options; never use disclosed hardship or a protected-class proxy to justify
  harsher treatment or as an eligibility penalty.
- **Affordability is indicative.** The disclosed surplus sizes an *indicative* arrangement; it
  is not a credit or affordability determination — route substantiation to the affordability
  skills.
- **Do not tune rules to a person.** Eligibility comes from the versioned config, not from
  guessing what "should" apply to this customer.
