---
name: sanctions-match-adjudicator
description: >-
  Adjudicate a sanctions/PEP screening HIT (potential match): resolve the subject against the
  matched listed entity, compute documented match factors (name/alias, identifiers, DOB,
  nationality, place of birth, address, ownership under the OFAC 50% Rule, transaction/
  jurisdiction context), assemble a durable, fully cited evidence bundle with a chronology, and
  produce a disposition RECOMMENDATION (true-match escalate / potential-match review / false-
  positive discount) for authorized review. Use when a sanctions analyst or payments
  investigator needs to work up a screening-filter or KYC-rescreening hit, decide whether a
  name is a real list match or a false positive, and hand an audit-ready package to a sanctions
  officer. This skill NEVER autonomously confirms or discounts a match, blocks, rejects,
  releases, or unblocks a payment or account, files a blocking/OFAC report, or closes a case —
  every disposition is a recommendation an authorized sanctions officer must adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires sanctions/PEP-screening, KYC/customer, transactions, case-management, and regulatory-corpus MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "Sanctions analyst / payments investigator"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Sanctions Match Adjudicator

## Purpose and outcome
Take a sanctions/PEP screening **hit** (a potential match between a subject — a customer,
counterparty, or a party in a payment — and a listed entity) and work it up into an
audit-ready case: resolve the subject against the matched listed entity, compute **documented,
explainable match factors** (corroborators and discriminators) across name/alias, identifiers,
date of birth, nationality, place of birth, address, ownership (OFAC 50% Rule), and
transaction/jurisdiction nexus, merge the dated evidence into a durable, time-ordered
**evidence bundle** with a chronology, link prior cases, and produce a disposition
**recommendation**. The outcome is a cited package a sanctions officer can adjudicate — the
substantive true/false-match determination, any payment block/reject/release, account
block/unblock, and any blocking/OFAC report stay with that authorized human.

## Use when
- "Adjudicate this OFAC screening hit — is it a real match or a false positive?"
- "Work up this payment-filter hit: build the chronology and factors and recommend a disposition."
- "Does the 50%-Rule ownership nexus make this counterparty a true match?"
- "This KYC-rescreening hit matches on name — do the identifiers discriminate it?"

## Do not use
- **First-line AML alert triage / queue prioritization** → `aml-alert-triager` (which routes a
  sanctions proximity flag here).
- **Onboarding/periodic list screening** that produces the hit → `kyc-customer-due-diligence-screener`.
- **Beneficial-ownership verification** of an ownership nexus → `beneficial-ownership-verifier`.
- **Adverse-media corroboration** on the subject → `adverse-media-investigator`.
- **Enhanced due diligence** packaging on a high-risk subject → `enhanced-due-diligence-packager`.
- Any request to **confirm/discount, block/reject/release, unblock, file, or close** → refuse;
  produce the recommendation and route to the authorized sanctions officer.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Screening, adjudication, and the
blocking/reporting decision are separate control activities. This skill **consumes a documented
screening hit**, emits a durable `case_id` + evidence bundle, and hands a **recommendation** to
a human; it never performs the screener's work or the officer's decision. A hit with no
screening provenance is refused (route back to the screening engine / `kyc-customer-due-diligence-screener`).

## Inputs and prerequisites
- The screening hit with `alert_id`, `screening_context`, `list_program`, **screening
  provenance** (`screening_engine`, `screening_run_id`), the `subject` record, the
  `matched_entity` list record, optional `transaction_context`, and prior cases. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to sanctions/PEP list data, KYC/customer, transactions, and case management.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The sanctions list data is the
authority for the listed entity; KYC for the subject; the screening engine for the hit and its
score; transactions for payment context; case management for prior cases and `case_id`. **Cite
every evidence item.** Match-factor weights and disposition bands are **versioned contracts**.

## Workflow
1. **Validate & establish provenance** — run `validate_input`. Fail closed if screening
   provenance is missing (a match must originate from a documented screening run, never be
   self-generated); warn on name-only subjects, sparse list entries, and missing dates.
2. **Resolve & build factors (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve the subject
   against the matched entity, compute each documented match factor with its weight, sign
   (corroborator/discriminator), and citations, and merge the dated evidence into one
   time-ordered chronology (every event cited). See [references/domain-rules.md](references/domain-rules.md).
3. **Derive the disposition RECOMMENDATION** — `needs-data` if the subject is name-only;
   `possible-duplicate` if it overlaps an open case (linked, not re-adjudicated); an **ownership
   (50% Rule)** or **strong-identifier + name** override recommends true-match escalate; a
   **conflict guard** routes conflicting strong signals to L2 review (never auto-discount);
   otherwise the score band maps to `recommend-true-match-escalate`,
   `recommend-potential-match-l2-review`, or `recommend-false-positive-discount`.
4. **Route where relevant** — attach lateral routing (UBO verification, adverse media, EDD) as
   recommendations, not actions.
5. **Never adjudicate** — no confirmation/discount, block/reject/release, unblock, filing, or
   closure.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen enforces: durable `case_id` (`SANC-<alert_id>`); screening provenance present;
disposition ∈ the allowed recommendation set; every chronology event, match factor, and party
cited; the `disposition_basis` ties out (score-band ↔ score; overrides require their factor;
the conflict guard requires a discriminator); and **no confirmation/discount/block/release/
filing language**. Fail closed on any miss.

## Human approval
`required`. Adjudication is decision-support: this skill proposes a disposition and assembles
cited evidence. **Every** true/false-match determination, payment block/reject/release, account
block/unblock, sanctions-list case closure, and blocking/OFAC (or connected SAR) filing is
decided by an authorized sanctions officer / OFAC compliance / MLRO through the approval broker.
The skill recommends; humans decide.

## Failure handling
- **Name-only subject** → `needs-data`; list exactly what discriminator is required; never
  confirm or discount a hit on name alone.
- **No screening provenance** → fail closed; route back to the screening engine /
  `kyc-customer-due-diligence-screener`. Do not adjudicate an undocumented "match".
- **Conflicting strong signals** (e.g., name + DOB match but identifier mismatch) → do not
  auto-discount; recommend L2/senior review.
- **Ambiguous / duplicate** → link as `possible-duplicate` for human confirmation; never
  auto-merge or re-adjudicate in parallel.
- **Sparse or stale list entry** → cite the list version and flag the gap; do not infer missing
  identifiers.
- **Tool timeout** → return the partial bundle with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Case list** — per case: `alert_id`, durable `case_id`, `list_program`, `screening_context`,
   `disposition_recommendation`, `disposition_basis`, `match_score` + reason.
2. **Evidence bundle** (per case) — subject + matched listed entity + ownership/transaction
   parties (masked) with roles; time-ordered chronology (each event cited); amounts (payment
   amount/currency, else null); match factors with weights and citations; linked cases; full
   citation list.
3. **Rationale** — recommendation tied to the corroborators/discriminators (recommendation language).
4. **Routing** — lateral/downstream handoffs where relevant.
5. **Machine-readable** — the case records + bundles keyed by durable `case_id`.
6. **Standing note** — "Sanctions adjudication decision-support only; no match has been confirmed
   or discounted, no payment has been blocked, rejected, or released, no account has been blocked
   or unblocked, and no blocking/OFAC report has been filed. An authorized sanctions officer must
   adjudicate every disposition."
See [references/controls.md](references/controls.md).

## Privacy and records
**Restricted.** Sanctions casework is sensitive: mask internal customer/account identifiers to
what evidences the match (the matched *name* is itself the evidence and is retained). Where an
adjudication connects to suspicious-activity reporting, **SAR-confidentiality / tipping-off**
controls apply — never produce customer-facing content revealing screening, blocking intent, or
SAR activity. Retain the evidence bundle, match-factor values, weights/config version, and
citations per sanctions recordkeeping; log analyst identity on every read and on the
recommendation.

## Gotchas
- **Factors are evidence, not a finding.** A corroborated identity is weight-of-evidence for a
  human; it is never a determination that the subject *is* the listed party.
- **Recommendation ≠ disposition.** `recommend-false-positive-discount` proposes a discount; the
  hit is only discounted when an authorized officer adjudicates it. Likewise a true-match
  recommendation never itself blocks a payment or files a report.
- **Never clear on name alone.** A name-only hit is `needs-data`; a matching name with a
  mismatching DOB/identifier is not a self-clear — the conflict guard sends it to L2 review.
- **The 50% Rule bites.** An entity owned ≥ 50% by a listed party is treated as a true-match
  escalation even when the entity itself is not named and its type differs from the owner's.
- **Provenance gates adjudication.** No documented screening run ⇒ do not adjudicate; a "match"
  you cannot trace to a screening hit is not one you may work.
- **Config is versioned.** Record the weights/bands version on every bundle so the recommendation
  is reproducible and reviewable.
