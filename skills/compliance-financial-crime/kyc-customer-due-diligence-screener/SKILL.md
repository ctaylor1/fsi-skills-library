---
name: kyc-customer-due-diligence-screener
description: >-
  Screen a customer or entity's KYC/CDD case for completeness, identity verification, risk
  factors (higher-risk jurisdiction/industry, PEP, adverse media), potential sanctions/
  watchlist matches, and beneficial-ownership coverage; produce explainable, source-linked
  findings and a deterministic recommended review track (Standard-CDD, Remediate-First,
  EDD-Recommended, or Escalate-For-Adjudication). Use when a KYC/onboarding analyst asks
  "screen this CDD file", "does this case need enhanced due diligence?", "what are the KYC
  risk factors and gaps here?", or needs a review-ready evidence pack before adjudication.
  This skill recommends and evidences only; it NEVER approves/rejects/onboards/exits a
  customer, adjudicates or clears a sanctions/PEP match, sets a customer risk rating, closes
  a case, or files a report — those are human/authorized-specialist actions.
license: MIT
compatibility: Amazon Quick Desktop; requires KYC/AML case, sanctions/PEP screening, adverse-media, beneficial-ownership/registry, transaction-monitoring, and versioned-config MCP integrations (all read-only).
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
  aws-fsi-primary-user: "KYC / client onboarding analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# KYC Customer Due Diligence Screener

## Purpose and outcome
Given a customer or entity's KYC/CDD case, compute a set of **explainable CDD signals**
(completeness, identity, risk factors, potential sanctions/PEP matches, beneficial-ownership
coverage), explain in plain language why each fired, attach cited evidence to each, and map
the fired set to a **deterministic recommended review track**. A successful output lets a
KYC / onboarding analyst see exactly what is complete, what is missing, and what elevates
risk — so the analyst can adjudicate. The **decision, disposition, rating, closure, and any
filing remain human** (R3 decision support).

## Use when
- "Screen this new customer/entity CDD file and show me the gaps and risk factors."
- "Does this onboarding case warrant enhanced due diligence?"
- "Are there PEP, sanctions, or adverse-media indicators on this case?"
- "Is beneficial ownership sufficiently identified and verified?"
- An analyst needs a consistent, cited CDD write-up to attach to a case before adjudication.

## Do not use
- The user wants a **CDD/KYC decision** ("approve/reject this customer", "onboard them",
  "exit the relationship") or a **customer risk rating set/updated** → out of scope; provide
  evidence + a recommended track and route to the human analyst. For a rating
  recalculation/challenge route to `customer-risk-rating-reviewer` (human-decided).
- A **sanctions/PEP potential match needs a disposition** → `sanctions-match-adjudicator`
  (adjudicated by a specialist + human). This skill never clears or confirms a match.
- **Enhanced due-diligence package assembly** (source of wealth/funds, ownership evidence) →
  `enhanced-due-diligence-packager`.
- **Ownership-chain mapping/verification** in depth → `beneficial-ownership-verifier`.
- **Adverse-media assessment** in depth → `adverse-media-investigator`.
- **Transaction-monitoring alert** work → `transaction-monitoring-alert-investigator`; a
  **SAR narrative** → `suspicious-activity-report-drafter` (draft-only, human-filed).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited evidence pack
with a durable `screening_id`; downstream adjudication/packaging/investigation skills consume
it. It must not duplicate their disposition, decision, or filing steps.

## Inputs and prerequisites
- The **case identifier** and the customer/entity record (type, legal name, jurisdiction,
  and for entities the industry and beneficial owners).
- **Documents** (type, issue/expiry dates, verification status), **identity checks**
  (attribute reconciliation across sources), and **screening indicators** (sanctions, PEP,
  adverse media) where available. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The versioned **config** (required fields/documents, UBO thresholds, higher-risk
  country/industry lists) — see [references/domain-rules.md](references/domain-rules.md).
- Read access to the KYC/AML case system and screening/registry sources.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The KYC/AML case system is the
record; sanctions/PEP/adverse-media sources contribute **potential indicators only**; the
registry corroborates ownership; config supplies thresholds/lists. Cite every signal's
evidence to a source row. A customer assertion never overrides the record or registry.

## Workflow
1. **Scope & load** — confirm the case and customer/entity; load documents, identity checks,
   screening indicators, and owners for the config version; validate with `validate_input`.
2. **Compute signals (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   configured completeness, identity, risk-factor, and beneficial-ownership signals. Each
   returns whether it fired plus the evidence rows behind it. Signals are **explainable**,
   not a black-box score, and never an automated risk rating.
3. **Assemble evidence** — for each fired signal, attach the specific record(s)/indicator(s)
   and the basis, with citations.
4. **Recommend a track** — map the fired-signal set to the deterministic review track
   (Standard-CDD / Remediate-First / EDD-Recommended / Escalate-For-Adjudication) per the
   documented mapping. This is a triage recommendation for a human, explicitly **not** a
   CDD decision, a rating, or a sanctions/PEP disposition.
5. **Write the pack** — plain-language explanation per signal + evidence + the recommended
   track + `recommended_next_steps` (human/specialist routing) + benign-explanation prompts
   and uncertainties to weigh.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired signal has evidence + citation, the
recommended track maps deterministically from the fired signals, `adjudication_required` is
true, no decision/closure/filing/disposition language is present, the standing disclaimer is
present, and routing next-steps accompany any elevated-risk or sanctions signal. Fail closed
on any miss.

## Human approval
`required`: a qualified KYC/onboarding analyst must adjudicate every finding before any CDD
decision, onboarding/exit, risk-rating write, sanctions/PEP disposition, case closure, or
filing. The skill delivers evidence and a recommended track only; it takes no action and
writes no system of record.

## Failure handling
- **Thin/incomplete case** (missing documents, no identity checks) → completeness/identity
  signals fire or are labelled low-confidence; do not overstate risk; list what is missing
  and recommend `Remediate-First`.
- **Ambiguous identity / entity resolution** → stop and confirm; never screen the wrong
  party or merge a same-name adverse-media hit without evidence.
- **Missing screening block** → compute only the signals the data supports; label the rest
  "not evaluable".
- **Stale/conflicting sources** → cite each; do not resolve silently.
- **Potential sanctions/PEP match** → never adjudicate; recommend `Escalate-For-Adjudication`
  and route to the specialist + human.
- **Tool timeout** → return partial signals computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — case, customer (masked where feasible), as-of, count of fired signals,
   recommended track, `adjudication_required: true`.
2. **Signals** — per fired signal: name, plain-language reason, evidence rows (cited), and
   the basis/threshold it deviates from.
3. **Consider (benign explanations)** — explicit alternative explanations so the analyst
   weighs both sides.
4. **Recommended next steps** — human/specialist routing (adjudication, EDD packaging, UBO
   verification, adverse-media assessment).
5. **Data gaps / not-evaluable signals.**
6. **Machine-readable** — signals + evidence + `screening_id` for downstream skills.
7. **Standing disclaimer** — recommendation only; not a KYC/AML decision; nothing onboarded,
   rated, closed, or filed; a qualified analyst must adjudicate.
See [references/controls.md](references/controls.md).

## Privacy and records
Restricted AML/BSA data with **SAR-confidentiality and tipping-off controls**: never disclose
a potential SAR-related concern to the customer. Minimize customer PII to what evidences a
fired signal; mask identifiers where feasible. Retain the screening + citations + config
version per records policy; log the read and any downstream adjudication/approval. Never
exfiltrate customer or screening data.

## Gotchas
- **A signal is not a decision.** Fired signals justify a *review track*, never a CDD
  approval/rejection, a risk rating, or a sanctions/PEP disposition.
- **Potential match ≠ finding.** Sanctions/PEP/adverse-media indicators are potential matches
  or allegations; the disposition is adjudicated by a specialist and a human.
- **Tipping-off risk.** Do not surface SAR-related suspicion to the customer or in
  customer-facing text.
- **UBO coverage vs. verification are different.** Below-coverage (owners not yet identified)
  and unverified (identified but not evidenced) are distinct signals — report both.
- **Same-name adverse media.** Resolve the entity before attaching an adverse-media hit; a
  name collision is a common false positive.
- **Do not tune thresholds/lists to a person.** Higher-risk lists and thresholds come from
  the versioned program config, not from what "should" be normal for this customer.
