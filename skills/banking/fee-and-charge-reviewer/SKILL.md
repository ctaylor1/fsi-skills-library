---
name: fee-and-charge-reviewer
description: >-
  Identify, categorize, and explain the fees and charges on a deposit or loan account,
  compare each against the account's disclosed fee schedule / product terms, and draft
  neutral questions or a remediation request for a customer or service agent. Use when a
  consumer, service agent, or reviewer asks "why was I charged this fee", "is this
  overdraft/maintenance/ATM/wire/late fee correct", "compare my fees to the disclosed
  schedule", or needs a review-ready fee-discrepancy pack. This skill compares fees to
  disclosed terms and drafts questions; it NEVER asserts a legal or regulatory violation,
  decides or promises a refund/credit/adjustment, reverses or waives a fee, or gives legal
  advice — those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking/fees, product-terms/fee-schedule, CRM, and loan origination/servicing MCP integrations (all read-only), plus the approved-calculation service.
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Consumer / customer-service agent"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Fee and Charge Reviewer

## Purpose and outcome
Given an account's posted fees and its **disclosed fee schedule / product terms**, categorize
each charge, compare it deterministically to the disclosed term (amount, frequency cap, waiver
condition), and produce a **review-ready pack** of cited findings, neutral questions, and a
remediation-**request** draft with a deterministic **review outcome**. A successful output
lets a customer understand a charge, or lets a service agent decide what to raise with
servicing — the decision, any refund/credit, and any fee action remain human.

## Use when
- "Why was I charged this fee?" / "Is this overdraft / maintenance / ATM / wire / late fee correct?"
- "Compare the fees on my statement to the disclosed schedule."
- "The account was charged a monthly fee — didn't direct deposit waive it?"
- A service agent needs a consistent, cited fee-vs-schedule write-up to attach to a case.

## Do not use
- The user wants a **refund/credit decision**, a fee **reversal/waiver**, or an assertion that
  a fee is **unlawful / violates** a regulation → out of scope. Provide the cited comparison
  and route to a human/authorized system.
- **Complaint** adjudication (chronology, applicable standards, proposed remediation, reviewed
  response) → `complaint-resolution-assistant`.
- **Loan-servicing** exception root-cause and staged correction → `loan-servicing-exception-resolver`.
- **Card transaction disputes** → `dispute-operations-assistant` (issuer/acquirer) or
  `chargeback-dispute-packager` (merchant).
- **Merchant** interchange/processor-pricing analysis → `merchant-fee-optimizer`.
- General statement/cash-flow analysis → `bank-statement-analyzer`; unusual/unauthorized
  **activity** (not a disclosed-fee question) → `account-anomaly-screener`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a fee-review pack with a
durable `review_id`; downstream complaint/servicing/dispute skills consume it. It must not
duplicate their decision, adjudication, or action steps.

## Inputs and prerequisites
- Account identifier and the **statement period** (or the specific charges) to review.
- **Posted fees** for the period, each with `fee_id`, date, amount, currency, `fee_code`
  (may be null if unmapped), and a `source_ref`.
- The **disclosed fee schedule / product terms** in effect for that period, each term with
  `fee_code`, label, category, `disclosed_amount`, optional `cap_per_day`/`cap_per_period`,
  optional `waiver_conditions`, and a `source_ref`.
- Optional **account context** (`waivers_met`: conditions the account satisfies, e.g.
  `direct_deposit`, `min_balance`). Read access to core-banking/fees, product terms, CRM, and
  loan servicing. Schema: [scripts/validate_input.py](scripts/validate_input.py); thresholds:
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **disclosed schedule** is the
comparison basis and the **posting** is the record of what was charged; CRM supplies waiver
context. Use the schedule **in effect for the statement period**, not the latest one. Cite
every finding to a posted row and, where a term exists, the disclosed term.

## Workflow
1. **Scope** — confirm the account, statement period, and the charges in question; load the
   posted fees and the disclosed schedule in effect; validate with `validate_input`.
2. **Compare (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to match each posted
   fee to its disclosed term and classify it (`matches_disclosed`, `exceeds_disclosed`,
   `frequency_cap_exceeded`, `waiver_condition_may_apply`, `not_in_schedule`). Each finding
   carries the evidence rows behind it. The comparison is **explainable**, not a score.
3. **Assemble evidence** — for each flagged finding, attach the posted row and the disclosed
   term it deviates from, with citations.
4. **Map outcome** — map the finding set to a **review outcome** (`no_discrepancies`,
   `questions_to_raise`, `discrepancies_found`) per the deterministic, documented mapping. This
   is a triage signal for a human, explicitly **not** a determination that a fee was improper.
5. **Draft questions & request** — write neutral questions (ask servicing to confirm the
   schedule version or whether a waiver applied) and a remediation-**request** draft, plus
   explicit uncertainties. Nothing here decides a refund or takes a fee action.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: every flagged finding has evidence + citation, the review outcome
maps deterministically from the findings, no violation/refund-decision/fee-action/legal-advice
language is present, the standing disclaimer is present, and questions plus a remediation
request accompany any flagged findings. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the pack, questions, or remediation request
are sent to a customer or written to a case/system of record. No approval is needed for the
agent's own read. The skill never takes a fee action.

## Failure handling
- **Missing/incomplete disclosed schedule** → compare only the fees with a matching term;
  label the rest `not_in_schedule`; do not infer the disclosed amount.
- **Ambiguous account/identity** → stop and confirm; never review the wrong account.
- **Wrong schedule version** → use the schedule in effect for the period; if unknown, state it
  and treat comparisons as low-confidence rather than guessing.
- **Missing waiver context** → do not assume a waiver was met; report the condition as
  unverified and ask.
- **Stale/conflicting sources** → cite both the posting and the term; do not resolve silently.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — account (masked), statement period, count of flagged findings, review outcome,
   and `total_flagged_for_review` (labeled "for review", not an amount owed).
2. **Findings** — per fee: category, status, posted vs disclosed amount, discrepancy amount,
   plain-language reason, and cited evidence (posted + disclosed).
3. **Questions** — neutral questions to raise with servicing for each flagged finding.
4. **Remediation-request draft** — a request for review a human must approve before delivery.
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Fee review and questions only; not a legal conclusion, refund
   decision, or legal advice, and not a reversal or credit of any charge."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/card numbers (last 4). Minimize customer data in output to what
evidences a flagged finding. Retain the review + citations + schedule/`config_version` per
records policy; log the read and any external-delivery approval. Never exfiltrate customer data.

## Gotchas
- **A discrepancy is not a violation.** "Posted amount exceeds the disclosed amount" is a
  question to raise, never a legal conclusion or a refund decision.
- **Schedule version matters**: comparing to the wrong (e.g., latest) schedule fabricates
  discrepancies. Use the version in effect for the statement period.
- **Waivers are conditional**: a met waiver condition means the fee *may* be waivable — ask;
  do not declare it wrongly charged.
- **Unmapped fees**: a `not_in_schedule` fee means the disclosed term wasn't provided, not that
  the fee is improper — request the term.
- **Do not net or "true up"**: report each finding and a "for review" total; never compute or
  promise an amount to be refunded or credited.
- **Frequency caps are per the disclosed unit** (per day vs per statement period) — apply the
  disclosed cap, not an assumed one.
