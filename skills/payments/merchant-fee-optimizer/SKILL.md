---
name: merchant-fee-optimizer
description: >-
  Analyze a merchant's card-processing statement: decompose fees into interchange, network
  assessments, and processor markup; quantify interchange downgrades, card mix, Level 2/3
  data opportunities, pricing model, and contract terms; and estimate transparent,
  assumption-backed savings opportunities with cited evidence. Use when a merchant or
  payments finance analyst asks "why is my effective rate so high", "where can I cut card
  processing fees", "are we getting hit with interchange downgrades", "should we look at
  interchange-plus", or wants a review-ready fee-optimization pack from a processing
  statement. This skill estimates savings as ranges and explains options; it NEVER
  guarantees savings, NEVER recommends or directs signing, terminating, or switching a
  processor or contract, NEVER gives legal, tax, or accounting advice, and takes no system
  action — those are human decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires processor/acquirer statement & settlement, gateway transaction-detail, card-network-rules/interchange-schedule, merchant-contract, and benchmarks-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant / payments finance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Merchant Fee Optimizer

## Purpose and outcome
Given a merchant's card-processing statement and transaction detail, **decompose the fees**
(interchange, network assessments, processor markup, fixed monthly fees), compute the
effective rate and implied markup, and produce a **review-ready fee-optimization pack**: a
set of **explainable, evidenced savings opportunities**, each with a transparent estimate
**range** and its stated assumptions. A successful output lets a merchant/payments analyst
understand where fees come from and quantify options to discuss — the **decision to change
anything (pricing, processor, contract) remains a human one**.

## Use when
- "Why is my effective rate so high?" / "Break down my processing fees."
- "Where can I cut card processing costs?" / "Find savings on this statement."
- "Are we getting hit with interchange downgrades?"
- "Should we look at interchange-plus instead of tiered pricing?"
- "Do our commercial-card transactions qualify for Level 2/3?"
- A payments analyst needs a consistent, cited fee write-up to attach to a client review.

## Do not use
- The user wants a **binding decision made or executed** — "pick a processor and sign us up",
  "cancel/terminate my contract", "switch us over" → out of scope. Estimate the options and
  route the decision to the human; the skill never signs, terminates, switches, or negotiates.
- **Legal/tax/accounting advice** on contract enforceability, surcharging legality, or
  accounting treatment → out of scope; surface terms factually and defer to counsel/tax.
- **Settlement/funding reconciliation** or break classification → `settlement-break-reconciler`
  or `transaction-reconciliation-helper`; **settlement report summary** → `settlement-report-summarizer`.
- **Chargeback/dispute** packaging → `chargeback-dispute-packager`.
- **Network-rule/interchange-schedule change** tracking → `network-rules-change-tracker`.
- **ISO 20022 message** field interpretation → `iso-20022-message-interpreter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a fee-optimization pack
with a durable `analysis_id`; downstream reconciliation, dispute, and rule-tracking skills
consume it. It must not duplicate their reconciliation, dispute, or action steps, and it
never performs a contract/processor action.

## Inputs and prerequisites
- **Merchant statement** for a stated period (YYYY-MM): volume, fee lines, and fixed monthly
  fees; and **transaction detail** with card type, entry mode, Level 1/2/3 status,
  interchange category, and per-transaction interchange/assessment/processor fees.
- Optional **contract terms** (pricing model, markup, term, auto-renew, early-termination
  fee) and **benchmarks config** (versioned). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to processor/settlement, gateway detail, card-network schedules, and config
  (see [references/domain-rules.md](references/domain-rules.md)). All read-only.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **processor statement/settlement
is the position of record** for what was charged; card-network interchange schedules and
rules are the authority for category qualification. Cite every opportunity to a transaction
or statement line; validate any downgrade or Level 2/3 estimate against the current schedule.

## Workflow
1. **Scope & validate** — confirm the merchant, statement period, and pricing model; load
   the statement and transaction detail; run `validate_input`. Note data gaps that limit
   evaluability (missing entry mode, missing `qualified_interchange_fee`, missing level).
2. **Decompose fees (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute volume,
   interchange, assessments, markup, fixed fees, effective rate, and implied markup.
3. **Estimate opportunities (deterministic)** — the same script computes the configured
   opportunities (`pricing_model_switch`, `downgrade_recovery`, `level_2_3_enablement`),
   each returning a point estimate, a **low-to-point range**, cited evidence, and its
   assumptions. Opportunities are explainable and additive — no opaque "you'll save X%".
4. **Add observations & contract flags** — effective-rate benchmark, fee mix, and factual
   contract flags (early-termination fee, auto-renew notice window) as context, **not advice**.
5. **Write the pack** — plain-language decomposition + each opportunity (estimate range,
   assumptions, evidence) + observations + explicit caveats + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired opportunity has cited evidence and ≥ 1
assumption; every estimate is a **range** (not a single guaranteed number); the totals
**tie out** to the sum of opportunities (annual = 12 × monthly); no guarantee / binding-
decision / legal-advice language is present; and the standing disclaimer is included. Fail
closed on any miss.

## Human approval
`external-delivery`: human review required before the pack is sent to the merchant/client or
written to a case/system of record. No approval is needed for the analyst's own read. The
skill never signs, terminates, switches, negotiates, or writes any system of record.

## Failure handling
- **Thin data** (few transactions, missing period totals) → state estimates are
  low-confidence; do not overstate savings; list what is missing.
- **Missing `qualified_interchange_fee` on downgraded rows** → report `downgrade_recovery`
  not-evaluable for those rows; never fabricate a downgrade cost.
- **Missing Level for commercial cards** → limit `level_2_3_enablement` evaluability; label it.
- **Stale/conflicting rates** (statement vs current schedule) → cite both; flag for the
  reviewer; do not silently "correct" the statement.
- **Tool timeout** → return the decomposition and opportunities computed so far with a clear
  "incomplete" flag; page long histories as resumable stages.

## Output contract
1. **Summary** — merchant (masked MID), period, volume, effective rate, total fees, and the
   combined estimated savings **range** (monthly and annual).
2. **Fee decomposition** — interchange / assessments / markup / fixed fees and shares.
3. **Opportunities** — per fired opportunity: description, estimate range (low → point),
   assumptions, and cited evidence rows.
4. **Observations & contract flags** — effective-rate benchmark, fee mix, factual contract
   terms (not advice), and any not-evaluable items.
5. **Machine-readable** — decomposition + opportunities + `analysis_id` for downstream skills.
6. **Standing disclaimer** — "Estimated savings and analysis only … not a guarantee of
   savings and not a recommendation to sign, terminate, or change any processor or contract …"
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer NPI/PII; cardholder data). **Mask the MID and any PAN to last
4; never emit full card numbers.** Operate on de-identified transaction detail. Minimize data
in the output to what evidences an opportunity. Retain the analysis + citations + config
version per records policy; log the read and any external-delivery approval. Never exfiltrate
cardholder or merchant data.

## Gotchas
- **An estimate is not a promise.** Savings depend on the stated assumptions and current
  network schedules; always present a range and require human review — never guarantee.
- **Interchange and assessments are pass-through.** Only the processor markup is truly
  negotiable; do not present interchange as "savings" the merchant can simply remove.
- **Effective rate is not a verdict.** A high effective rate can reflect card mix, ticket
  size, or channel (e.g., keyed/e-commerce), not just pricing — say so.
- **Do not double count.** `downgrade_recovery` (fixing existing categories) and
  `level_2_3_enablement` (unlocking commercial programs) are distinct; keep them separate.
- **Surcharging/cash-discount/steering** have network-rule and legal constraints — flag them
  for the merchant's own compliance/legal review; do not recommend them.
- **Contract terms are factual, not legal advice.** Surface early-termination fees and notice
  windows so the human can weigh them; never opine on enforceability.
- **Benchmarks are versioned config**, never tuned to the individual merchant.
