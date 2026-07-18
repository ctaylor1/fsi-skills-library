---
name: merchant-onboarding-risk-reviewer
description: >-
  Review a merchant onboarding application end to end — KYB and legal-entity resolution,
  beneficial ownership, business-model/MCC classification, expected activity, website and
  products, prohibited-use, sanctions and adverse-media screening status, fraud, and credit
  — then assemble a source-cited evidence package with a deterministic recommendation band
  and required conditions for an authorized adjudicator. Use when a merchant-risk,
  underwriting, or KYB analyst asks to review or risk-assess a new merchant application,
  evaluate onboarding risk, check prohibited/restricted business models, or prepare an
  approval evidence package. HARD BOUNDARY: this is R3 decision-support — it recommends and
  evidences only; it NEVER approves, declines, boards, or onboards a merchant, adjudicates a
  sanctions/adverse-media hit, closes the case, or files/writes any system of record. Human
  adjudication is required.
license: MIT
compatibility: Amazon Quick Desktop; requires KYB/registry, sanctions & adverse-media screening, merchant-application, website/product-review, fraud/credit, and controlled-rules (config) MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant-risk / underwriting / KYB analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Merchant Onboarding Risk Reviewer

## Purpose and outcome
Given a merchant onboarding application and its supporting evidence, compute a set of
**explainable risk findings** across KYB / beneficial ownership / business model / expected
activity / sanctions / adverse media / credit / prohibited-use, attach cited evidence to
each fired finding, check evidence completeness, and produce a **recommendation band**
(Approve / Approve-with-Conditions / Decline / Escalate-Insufficient-Evidence) with required
pre-boarding conditions. A successful output lets a merchant-risk adjudicator decide quickly
and defensibly — the onboarding decision, and any boarding/filing action, remains human.

## Use when
- "Risk-review this new merchant application / underwrite this merchant."
- "Does this merchant's business model / MCC hit a prohibited or restricted list?"
- "Assemble the onboarding evidence package and a recommendation for the risk committee."
- "Is the beneficial ownership / sanctions / adverse-media picture complete for boarding?"

## Do not use
- The user wants the **onboarding decision made**, the merchant **boarded/declined**, the
  case **closed**, or a **SAR/network submission filed** → out of scope. Provide the evidence
  package and route to the human adjudicator / authorized system.
- **Adjudicate a sanctions or adverse-media hit** → `sanctions-match-adjudicator` /
  `adverse-media-investigator` (this skill consumes their status, it does not clear a hit).
- **Verify beneficial ownership** to resolution, or run **CDD/EDD** → `beneficial-ownership-verifier`,
  `kyc-customer-due-diligence-screener`, `enhanced-due-diligence-packager`.
- **Material credit write-up** for a large requested limit → `credit-memo-drafter`.
- **Post-boarding** transaction risk monitoring or fraud investigation →
  `real-time-payment-risk-monitor` / `payment-fraud-case-investigator`.
- **Stablecoin/crypto settlement control review** → `stablecoin-payment-controls-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an evidence package
with a durable `review_id`; specialist screens and the human adjudicator consume it. It must
not duplicate their adjudication, decision, or action steps.

## Inputs and prerequisites
- The **merchant application** (`case_id`) with legal name, country, MCC, business model,
  website, expected monthly volume / average ticket, and requested processing limit.
- **Beneficial owners** with ownership %, country, verification status, and PEP flag.
- **Screening results**: sanctions status (`cleared`/`hit`/`pending`) and adverse-media
  status (`none`/`resolved`/`unresolved`) for entity and owners.
- **Evidence items**: KYB registration, UBO verification, website review, expected-activity
  substantiation, financials.
- Optional **credit** assessment; approved **config** (prohibited/restricted MCC lists,
  high-risk geographies, thresholds — see [references/domain-rules.md](references/domain-rules.md)).
- Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The KYB registry is the position of
record for entity and ownership; screening services own sanctions/adverse-media status;
network & prohibited-use rules are a versioned contract. Cite every finding's evidence to a
source record. Never substitute an applicant assertion for the registry or screening record.

## Workflow
1. **Scope & validate** — confirm the `case_id` and load the application, ownership,
   screening, evidence, and config; run `validate_input`. Resolve the entity/owners via
   entity-resolution before computing.
2. **Compute findings (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   configured findings. Each returns fired/not-fired, a plain-language reason, cited
   evidence, and its rule reference. Findings are **explainable**, not a black-box score.
3. **Check evidence completeness** — record which required items are present/missing; a gap
   drives Escalate-Insufficient-Evidence unless a blocking finding already governs.
4. **Map to a recommendation (deterministic)** — blocking → Recommend-Decline; incomplete →
   Escalate-Insufficient-Evidence; elevated → Recommend-Approve-with-Conditions (with a
   condition per fired elevated finding); none → Recommend-Approve. This is a recommendation
   for a human, explicitly **not** an onboarding decision.
5. **Assemble the package** — plain-language write-up per fired finding + evidence + the
   recommendation + required conditions + open items to route to specialist screens.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen confirms: `fired_findings` ties out to `findings[].fired`, every
fired finding has cited evidence, the recommendation equals the deterministic mapping,
`adjudication_required` is `true`, Approve-with-Conditions carries conditions, no
onboarding-decision/closure/filing language is present, and the standing disclaimer is
present. Fail closed on any miss.

## Human approval
`required`: a merchant-risk adjudicator (or the delegated authority / risk committee) must
decide before any approval, decline, boarding, condition sign-off, filing, or system-of-record
change. This skill produces the recommendation and evidence only; it takes no onboarding
action and records no decision.

## Failure handling
- **Missing/insufficient evidence** → findings for absent data are reported not-fired-but-
  not-evaluable via input warnings; the recommendation escalates as Insufficient-Evidence.
- **Ambiguous entity/ownership** → stop and confirm; never review the wrong legal entity.
- **Sanctions/adverse-media `hit` or `pending`** → treat as blocking / unresolved; do not
  clear it — route to the specialist adjudicator.
- **Stale screening** → a stale screen is a data gap, not a clearance; surface it.
- **Stale/conflicting sources** (application vs registry) → cite both; do not resolve silently.
- **Tool timeout** → return the findings computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — merchant (legal name, country, MCC, business model), count of fired
   findings, recommendation band.
2. **Findings** — per fired finding: name, severity, plain-language reason, cited evidence
   rows, and rule reference.
3. **Evidence completeness** — required vs present vs missing items.
4. **Recommendation & conditions** — the deterministic band and, for Approve-with-Conditions,
   the pre-boarding conditions; plus open items routed to specialist screens.
5. **Machine-readable** — findings + evidence + `review_id` for the adjudicator and
   downstream skills; `adjudication_required: true`.
6. **Standing disclaimer** — "Recommendation and evidence only; not an onboarding decision.
   No approval, decline, boarding, filing, or system-of-record change has been made. Human
   adjudication is required."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer NPI/PII; cardholder data). Minimize owner PII to what evidences
a fired finding; reference registry/screening records by ref. Retain the review + citations +
`config_version` per records policy; log the read and (via the approval broker) the
adjudicator's decision. Never exfiltrate applicant or owner data.

## Gotchas
- **A finding is not a decision.** Blocking findings justify a *Decline recommendation*,
  never an executed decline or a statement that the merchant "has been declined".
- **Screening status is consumed, not adjudicated.** `cleared` comes from the screening
  service; this skill never clears a `hit`/`pending` itself.
- **Restricted ≠ prohibited.** A restricted MCC is approvable with conditions; only the
  prohibited list blocks. Keep the two config lists distinct and versioned.
- **High-risk geography / PEP drive EDD, not intent.** Describe factually; the adjudicator
  weighs mitigants. Never use protected-class attributes or proxies as findings.
- **Ownership coverage traps.** Compute verified coverage against the required %; a single
  unverified >= threshold owner is a gap even if total coverage looks high.
- **Do not tune thresholds to the applicant**; thresholds/lists come from the versioned
  config, not from guessing what "should" be acceptable for this merchant.
