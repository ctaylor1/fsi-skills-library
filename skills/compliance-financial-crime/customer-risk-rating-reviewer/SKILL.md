---
name: customer-risk-rating-reviewer
description: >-
  Recompute and challenge a customer's KYC/AML risk rating against the approved weighted-factor
  methodology, then surface explainable, source-linked findings: rating discrepancies, mandatory
  risk floors (PEP/sanctions), expired or undocumented overrides, unassessed trigger events, and
  factor data-quality gaps, mapped to a deterministic recommended review outcome (Align-No-Change,
  Re-Rate-Recommended, Remediate-Data-First, or Escalate-For-Adjudication). Use when a KYC QA or
  compliance officer asks "recalculate this customer's risk rating", "does the current rating still
  hold?", "why is this customer rated Low when the factors look High?", "is this override still
  valid?", or needs a review-ready evidence pack before a periodic-review adjudication. This skill
  recomputes, evidences, and recommends only; it NEVER sets or changes a risk rating, approves or
  validates an override, disposes of a trigger, closes a review/case, or files anything — those are
  human/authorized-specialist actions.
license: MIT
compatibility: Amazon Quick Desktop; requires KYC/AML case, sanctions/PEP screening, transaction-monitoring, adverse-media, records-archive, and versioned methodology-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "KYC quality assurance / compliance officer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Customer Risk Rating Reviewer

## Purpose and outcome
Given a customer's risk-rating case (the scored risk factors, the rating of record, any
documented overrides, and recent trigger events), **recompute the model-derived (inherent)
risk band** from the approved weighted-factor methodology, **challenge** it against the
rating of record, and assemble **explainable, cited findings** — rating discrepancies,
mandatory risk floors, expired/undocumented overrides, unassessed triggers, and factor data
quality — mapped to a **deterministic recommended review outcome**. A successful output lets
a KYC QA or compliance officer see exactly why a rating does or does not hold and what to do
next. The **rating decision, override approval, trigger disposition, closure, and any filing
remain human** (R3 decision support).

## Use when
- "Recalculate this customer's risk rating and tell me whether the current band still holds."
- "Challenge / QA this periodic-review rating — the factors look higher than the record."
- "Is this downgrade override still valid, or has it lapsed?"
- "There's a new adverse-media / sanctions / jurisdiction trigger — does it force a re-rating?"
- A reviewer needs a consistent, cited rating write-up to attach to a case before adjudication.

## Do not use
- The user wants a **rating decision or write** ("set the rating to High", "confirm Low",
  "update the KYC record"), an **override approved/validated**, a **trigger disposed**, or a
  **review/case closed** → out of scope; provide the recomputation + findings and route to the
  human adjudicator. This skill never writes the system of record.
- A **new-customer / onboarding CDD screen** (completeness, identity, UBO coverage) →
  `kyc-customer-due-diligence-screener`. This skill reviews an existing rating, not onboarding.
- A **potential sanctions/PEP match needs a disposition** → `sanctions-match-adjudicator`.
- **Enhanced due-diligence package assembly** (source of wealth/funds, ownership evidence) →
  `enhanced-due-diligence-packager`.
- **Adverse-media assessment** in depth → `adverse-media-investigator`; **ownership-chain**
  mapping/verification → `beneficial-ownership-verifier`.
- A **transaction-monitoring alert** → `transaction-monitoring-alert-investigator`; a **SAR
  narrative** → `suspicious-activity-report-drafter` (draft-only, human-filed).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited **rating-review
pack** with a durable `review_id`; upstream triage/CDD skills feed it and downstream
adjudication/packaging/investigation skills consume it. It must not duplicate their decision,
disposition, or filing steps.

## Inputs and prerequisites
- The **customer identifier** and the **rating of record** (band, effective date, source_ref).
- The **scored risk factors** (factor, value, risk_value, weight, scale_max, observed_date,
  source_ref) for the approved methodology; **documented overrides** (from/to band, rationale,
  approver_role, approved/expiry dates); and recent **trigger events** (type, date, severity,
  assessed). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The versioned **methodology config** (factor catalog, weights, band thresholds, mandatory
  floors, staleness window) — see [references/domain-rules.md](references/domain-rules.md).
- Read access to the KYC/AML case system, screening/monitoring sources, and the config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The KYC/AML case system holds the
rating of record and factor values; the versioned methodology config supplies weights,
thresholds, and floors; screening/monitoring/adverse-media sources contribute **potential
trigger indicators only**. Cite every finding to a source row. A customer or RM assertion
never overrides the record, the registry, or the methodology.

## Workflow
1. **Scope & load** — confirm the customer and the rating of record; load factors, overrides,
   and triggers for the methodology version; validate with `validate_input`.
2. **Recompute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   weighted score, apply mandatory floors, and derive the recomputed band. The score is an
   **explainable weighted sum**, never a black-box rating, and is never tuned to the individual.
3. **Challenge & assemble findings** — compare the recomputed band to the rating of record and
   emit cited findings (rating_discrepancy, mandatory_floor, expired/undocumented_override,
   unassessed_trigger, stale/missing factor), each with the evidence behind it.
4. **Map the outcome** — map the findings to the deterministic review outcome
   (Align-No-Change / Re-Rate-Recommended / Remediate-Data-First / Escalate-For-Adjudication)
   per the documented precedence. This is a recommendation for a human, explicitly **not** a
   rating decision, an override approval, or a trigger disposition.
5. **Write the pack** — plain-language recomputation + findings + the recommended outcome +
   `recommended_next_steps` (human/specialist routing) + uncertainties and benign explanations
   to weigh.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every finding has evidence + citation, `recomputed_band`
ties out to the deterministic band mapping (score + floor), the review outcome maps
deterministically from the findings, a `rating_discrepancy` finding exists whenever the
recomputed band diverges from the record, `adjudication_required` is true, no
decision/closure/filing/override-approval language is present, the standing disclaimer is
present, and routing next-steps accompany any non-align outcome. Fail closed on any miss.

## Human approval
`required`: a qualified compliance officer / MLRO must adjudicate every finding before any
rating change, override approval, trigger disposition, periodic-review closure, or filing. The
skill delivers a recomputation, cited findings, and a recommended outcome only; it takes no
action and writes no system of record.

## Failure handling
- **Missing required factor** → the recomputation is low-confidence; emit
  `missing_required_factor`, recommend `Remediate-Data-First`, and do not overstate the band.
- **Ambiguous customer / entity resolution** → stop and confirm; never re-rate the wrong party.
- **Stale factors** → flag `stale_factor`; the value is still used but the reviewer is warned
  to refresh it before relying on it.
- **Potential sanctions/PEP match behind a factor** → never adjudicate; recommend
  `Escalate-For-Adjudication` and route to the specialist + human.
- **Stale/conflicting sources or methodology versions** → cite each; do not resolve silently.
- **Tool timeout** → return the partial recomputation computed so far with a clear
  "incomplete" flag; never guess the missing factors.

## Output contract
1. **Summary** — customer (masked), as-of, methodology version, score, recomputed band vs
   rating of record, recommended outcome, `adjudication_required: true`.
2. **Findings** — per finding: id, type, severity, plain-language description, and cited
   evidence rows; the factor detail behind the score.
3. **Consider (benign explanations)** — explicit alternatives (a valid current override, an
   already-planned periodic review, a same-name adverse-media collision) so the reviewer
   weighs both sides.
4. **Recommended next steps** — human/specialist routing (adjudication, EDD packaging,
   sanctions/adverse-media assessment, data remediation).
5. **Machine-readable** — recomputation + findings + `review_id` for downstream skills.
6. **Standing disclaimer** — recommendation only; not a rating decision; nothing rated,
   approved, disposed, closed, or filed; a qualified compliance officer must adjudicate.
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted AML/BSA data with **SAR-confidentiality and tipping-off controls**: never disclose
a potential SAR-related concern to the customer. Minimize customer PII to what evidences a
finding; mask identifiers to the last 4 where feasible. Retain the recomputation + citations +
methodology version per records policy so a review is reproducible; log the read and any
downstream adjudication/approval. Never exfiltrate customer or screening data.

## Gotchas
- **A recomputation is not a decision.** A divergent band justifies *a recommended re-rating
  for a human*, never an autonomous rating change, override approval, or closure.
- **The score is not the whole rating.** Mandatory floors (PEP → at least High, sanctions
  nexus at max → Prohibited) can raise the band above the weighted score; report both.
- **Overrides are load-bearing.** A record that sits below the recomputed band often rests on
  an override — always check its approver, rationale, and expiry; a lapsed override is a finding,
  not a silent justification.
- **Trigger ≠ disposition.** An adverse-media/sanctions/monitoring trigger is a *potential*
  reason to re-rate; the disposition is adjudicated by a specialist and a human.
- **Tipping-off risk.** Do not surface SAR-related suspicion to the customer or in
  customer-facing text.
- **Do not tune weights/thresholds/floors to a person.** They come from the versioned program
  methodology, not from what "should" be normal for this customer.
