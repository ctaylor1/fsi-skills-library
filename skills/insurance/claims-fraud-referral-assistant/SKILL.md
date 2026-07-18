---
name: claims-fraud-referral-assistant
description: >-
  Identify potential insurance-claim fraud indicators (red flags), assemble the supporting
  evidence with citations, score them against an approved versioned indicator set, and draft
  a Special Investigations Unit (SIU) referral package from a controlled template. Use when a
  claims adjuster or SIU intake needs to prepare a fraud referral, evaluate red flags on a
  suspicious claim, or package evidence for SIU review. This skill NEVER makes a fraud finding
  or determination, never denies/closes/voids a claim or takes any adverse customer decision,
  never accepts a referral or acts on SIU's behalf, and never sends the referral — it drafts
  a recommendation and evidence bundle for mandatory human adjudication; anything beyond the
  approved indicator set or draft-only scope fails closed.
license: MIT
compatibility: Amazon Quick Desktop; requires claims-administration, policy-administration, underwriting-rules/reference-data, document-intelligence, producer/third-party, and actuarial/catastrophe MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "SIU investigator / claims adjuster"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claims Fraud Referral Assistant

## Purpose and outcome
Take a claim (or a small batch of candidates) and produce an audit-ready **draft SIU fraud
referral**: evaluate only the documented, versioned fraud indicators (red flags), score them
explainably, recommend a routing disposition, and — for referrals — assemble a cited evidence
package from the approved template. The outcome is a referral a human SIU investigator can act
on quickly; the substantive fraud determination and every claim decision stay with people.

## Use when
- "Prepare a fraud referral for this claim / package this for SIU."
- "What red flags does this suspicious claim show?"
- "Score these flagged claims and draft referrals for the ones that warrant SIU review."
- "Assemble the evidence and chronology for an SIU intake."

## Do not use
- **Make a fraud finding / determination** → not permitted here (human SIU only).
- **Deny, close, rescind, or void a claim/policy**, or any adverse customer decision → refuse.
- **Third-party recovery** rather than fraud → `subrogation-opportunity-screener`.
- **Coverage/reserve or documentation review** of the file → `claims-file-reviewer`.
- **Claim intake/severity routing** → `claims-triage-assistant`.
- Any request to **accept a referral, decide it, or send it** → refuse; a human routes it.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Referral drafting is separated from SIU
investigation and from claim adjudication (different entitlements and outcomes). This skill
emits a durable `referral_id` + draft package; the SIU handoff is to a **human** specialist —
no catalog skill makes a fraud finding, and this skill must not simulate one.

## Inputs and prerequisites
- The claim(s) with `claim_id`, insured/policy refs, peril, loss and report dates, policy
  inception (and any coverage increase), prior-claims count, police/fire-report and
  documentation flags, statement-inconsistency count, lapse/reinstatement and prior-SIU flags,
  and source refs; plus the **approved indicator config** (versioned). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to claims administration, policy administration, underwriting/reference data,
  document intelligence, and producer/third-party history.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Claims administration is the system
of record for claim state; policy administration for coverage facts. Cite every evidence item.
The fraud-indicator config is a **versioned contract** recorded on each referral.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm required claim/policy fields and
   date sanity; flag data gaps that force `needs-data`.
2. **Evaluate indicators (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): evaluate ONLY the
   approved `FR-*` indicators, each with evidence and a citation; compute an explainable score.
3. **Band & recommend** — map the score to a band and a routing recommendation
   (`refer-to-siu` | `monitor` | `insufficient-indicators` | `needs-data`). A prior-SIU flag
   overrides to `refer-to-siu` for human intake.
4. **Draft the referral** — for `refer-to-siu`, assemble the package and draft the document
   from [assets/output-template.md](assets/output-template.md): masked insured, chronology,
   indicators, citations, and required approvals recorded as **pending**.
5. **Never decide** — no fraud finding, denial, closure, void, SIU acceptance, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: only allowed recommendations; approved indicator IDs with
evidence + citation; band ties to the deterministic mapping; each referral carries a complete
cited package and a template-faithful document; approvals recorded as pending (never granted);
no fraud-finding/denial/closure/void or accusatory customer-facing language; standing note
present. Fail closed on any miss.

## Human approval
`required`. Every referral is a **recommendation with evidence** for a licensed SIU
investigator / adjuster to adjudicate. This skill proposes and packages; the fraud
determination, any claim decision, and the act of routing/sending are human. Required
approvals (adjuster attestation, SIU intake acknowledgment) are drafted as **pending**.

## Failure handling
- **Unresolvable data** (missing inception/reportable classification) → `needs-data`; list
  exactly what is missing; do not guess to reach a recommendation.
- **Ambiguous identity/party** → cite what is known; do not infer intent.
- **Stale/conflicting sources** → cite both; prefer the system of record; surface the conflict.
- **Below threshold** → `monitor` or `insufficient-indicators` — a routing recommendation, not
  a clearance; no case is closed.
- **Tool timeout** → return partial scoring with an explicit incomplete flag; no retry
  assumption; never emit a referral off incomplete evidence.

## Output contract
1. **Referral queue view** — per claim: `referral_id`, recommendation, score + band, triggered
   indicator IDs, one-line cited rationale.
2. **Referral package** (per `refer-to-siu`) — masked insured, policy/peril, loss/report dates,
   chronology, indicators with evidence, citations, and required approvals (pending).
3. **Drafted referral document** — from the approved template, all required sections present.
4. **Data gaps / needs-data list.**
5. **Machine-readable** — the referral records keyed by `referral_id`.
6. **Standing note** — "Draft fraud referral only; no fraud finding has been made, no claim has
   been denied or closed, and no adverse customer decision has been taken. SIU adjudication and
   any decision require human review."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential — customer NPI/PII.** Mask insured/claimant identifiers to what
evidences the indicator; do not expose full identifiers in the referral body. Fraud referrals
carry anti-defamation and potential legal-privilege sensitivity — treat drafts as restricted
SIU work product, never customer-facing. Retain drafts, indicator evidence, and citations with
the indicator-config version per the insurer's anti-fraud recordkeeping; log adjuster identity
on every read and draft.

## Gotchas
- **Indicators are red flags, not findings.** A high score means "refer for human review," not
  "fraud." Never let the score read as a determination.
- **Draft-only.** The skill never sends, submits, or routes the referral itself — a human does.
- **Approvals stay pending.** The skill never records adjuster/SIU approval as granted; doing
  so would fake the human gate.
- **No customer accusation.** Never draft text telling or implying to the insured that they
  committed fraud — defamation and tipping-off risk.
- **Config is versioned.** Record the indicator-config version on every referral so the score
  is reproducible and reviewable.
- **Below-threshold ≠ cleared.** `monitor`/`insufficient-indicators` is a routing call a human
  may revisit; it closes nothing.
