---
name: stablecoin-payment-controls-reviewer
description: >-
  Review a stablecoin payment or settlement workflow against reserve, custody, screening,
  transaction, operational, reconciliation, and disclosure controls; surface pass/fail/gap
  findings with cited evidence, compute per-category coverage, and suggest a review
  disposition. Use when a payments risk, compliance, or treasury reviewer asks "review our
  stablecoin controls", "where are the control gaps before launch", "check reserve backing
  and travel-rule coverage", or needs a cited control-findings pack for adjudication. This
  skill evidences findings and recommends next steps only; it NEVER approves a launch,
  attests compliance, makes a sanctions/AML determination, closes a finding, files, or
  writes a system of record — those are human/authorized-system actions (R3).
license: MIT
compatibility: Amazon Quick Desktop; requires payment gateway/processor, fraud platform, settlement, network-rules, ISO 20022 parser, case-management, and ledger MCP integrations (all read-only), plus approved-config retrieval.
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
  aws-fsi-primary-user: "Payments product risk / compliance / treasury"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Stablecoin Payment Controls Reviewer

## Purpose and outcome
Given a stablecoin payment/settlement program's control attestation, evaluate each control
against its documented requirement, derive an explainable finding (`pass` / `fail` / `gap` /
`not_evaluable`) with an evidence citation, compute per-category coverage, and map the
finding profile to a **suggested review disposition** band. A successful output lets a
payments risk, compliance, or treasury reviewer see exactly which controls are evidenced,
which are deficient, and what to escalate — the **decision, adjudication, and any filing
remain human** (R3).

## Use when
- "Review our stablecoin (USDC/USDX-style) payment workflow controls and cite the evidence."
- "Where are the control gaps before we launch / expand this stablecoin rail?"
- "Check reserve backing, attestation currency, sanctions/wallet screening, and travel-rule
  coverage."
- "Reconcile-control review: does on-chain tie to the ledger within tolerance?"
- A reviewer needs a consistent, cited control-findings pack to attach to a program review
  or exam file.

## Do not use
- The user wants an **approval, launch sign-off, or compliance attestation** ("approve the
  program", "certify we're MiCA/GENIUS-compliant") → out of scope; produce evidence and
  route to the accountable human owner. This skill never approves, attests, or closes.
- A **sanctions/wallet match** needs adjudication → `sanctions-match-adjudicator`.
- A **transaction-monitoring/AML alert** needs investigation → `aml-alert-triager` then
  `transaction-monitoring-alert-investigator` (SAR drafting is `suspicious-activity-report-drafter`,
  draft-only, human-filed).
- An **on-chain vs ledger break** needs resolution → `settlement-break-reconciler` or
  `transaction-reconciliation-helper`; GL tie-out → `gl-reconciler`.
- A **payment failure/exception** needs diagnosis or repair → `payment-failure-diagnoser`,
  `payment-exception-investigator`, `payment-repair-assistant`.
- Parse a raw **ISO 20022** message → `iso-20022-message-interpreter`.
- Custodian/reserve-bank **third-party risk** due diligence → `third-party-risk-assessor`.
- **Regulatory reporting** data validation → `regulatory-reporting-data-validator`; new
  stablecoin-rule impact → `regulatory-change-impact-analyzer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a control-findings
pack with a durable `review_id`; downstream adjudication, investigation, reconciliation, and
reporting skills consume the finding + evidence. It must not duplicate their determination,
resolution, or filing steps.

## Inputs and prerequisites
- The program identifier and the **control attestation** for the period: one row per control
  with `id`, `category`, optional `attested`, the `metrics` that control needs, and a
  `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py); control
  catalog and rules: [references/domain-rules.md](references/domain-rules.md).
- The **config version** (thresholds: backing ratio, attestation cadence, travel-rule max,
  minimum confirmations, reconciliation tolerance, report cadence). Thresholds are a
  versioned contract, not per-program guesses.
- Read access to the systems in [references/source-map.md](references/source-map.md)
  (attestations, custody/trust agreements, screening config, settlement/recon reports,
  disclosures). All read-only.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The independent reserve
attestation and executed custody/trust agreements are the position of record; screening and
risk configuration, settlement/reconciliation reports, and published disclosures evidence
the remaining controls; the versioned threshold config governs pass/fail. Cite every finding
to a source `source_ref`. If sources conflict, cite both and flag for the reviewer — never
resolve silently.

## Workflow
1. **Scope & validate** — confirm the program, period (`as_of`), and jurisdiction; load the
   attestation; run `validate_input`. Fail closed on structural problems; note evaluability
   warnings and any missing critical controls.
2. **Evaluate controls (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to apply each
   control's documented rule, deriving `pass`/`fail`/`gap`/`not_evaluable` with the observed
   values and an evidence citation. Findings are **explainable**, not a black-box score.
3. **Assemble evidence** — for each finding (fail/gap) attach the specific `source_ref` and
   the requirement it deviates from; compute per-category coverage.
4. **Suggest disposition** — map the finding profile to a band (Controls Evidenced /
   Findings - Remediation Recommended / Material Gaps - Escalate) per the deterministic,
   documented mapping. This is a **triage suggestion for a human**, explicitly not an
   approval, attestation, or compliance determination.
5. **Write the pack** — plain-language finding per control + evidence + coverage + the
   suggested disposition + remediation prompts routed to the accountable owner + explicit
   not-evaluable items and uncertainties.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every finding has a cited evidence row, the disposition
ties out to the deterministic mapping, **no approval/attestation/closure/filing language is
present**, the standing disclaimer is included, and remediation prompts are present when any
finding fired. Fail closed on any miss.

## Human approval
`required` (R3): human adjudication is mandatory before any regulated decision, launch
approval, compliance attestation, case closure, filing, or system-of-record write based on
this review. The skill produces evidence and a recommendation for that human; it takes no
such action itself and stages nothing for execution.

## Failure handling
- **Missing / unattested critical control** (reserve backing, reserve quality, attestation
  currency, qualified custody, sanctions screening, travel rule, on-chain reconciliation) →
  report as `gap`/`not_evaluable` and escalate; do not assume other controls compensate.
- **Insufficient metrics** for a control → mark `not_evaluable` with the missing field; do
  not infer a pass.
- **Ambiguous program/period** → stop and confirm; never review the wrong program or period.
- **Stale attestation** (age over the configured max) → the attestation-currency control
  fails; still cite the stale document and its date.
- **Stale/conflicting sources** → cite both; do not resolve silently.
- **Tool timeout** → return the controls evaluated so far with a clear "incomplete" flag;
  never imply full coverage.

## Output contract
1. **Summary** — program, period, jurisdiction, config version, count of findings, suggested
   disposition band.
2. **Findings** — per fail/gap control: id, category, requirement, observed values, plain
   reason, and the cited `source_ref`.
3. **Coverage** — per-category pass/total, and the `not_evaluable` list with reasons.
4. **Remediation prompts** — next steps routed to the accountable control owner (human
   adjudication), not actions taken.
5. **Machine-readable** — controls + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Control-review evidence only; not a compliance determination,
   launch approval, or attestation. No finding has been closed and no filing or
   system-of-record change has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer NPI/PII; cardholder data). Keep customer/counterparty data out
of the control pack except where a `source_ref` requires it; never place wallet addresses,
PANs, or PII in narrative free-text. Retain the review + citations + config version per
records policy; log the read and any human adjudication. Never exfiltrate program or
customer data.

## Gotchas
- **A finding is not a decision.** A failed critical control justifies *escalation*, never a
  compliance conclusion, launch approval, or account/program action.
- **Backing ratio uses market value vs. par-valued outstanding tokens.** A par-value config
  mismatch silently distorts the ratio; record the config version so the review reproduces.
- **Attestation age is measured to `as_of`, not today.** A review of a past period must use
  that period's `as_of`, or currency findings will be wrong.
- **Travel-rule "enabled" is not enough** — a threshold above the required max is an
  under-scoped control (`gap`), not a pass.
- **Screening/sanctions wording is sensitive**: report the control state factually
  ("screening not enabled"); do not assert a sanctions violation or a hit disposition — that
  is `sanctions-match-adjudicator`'s human-adjudicated call.
- **Do not tune thresholds to a program**: thresholds come from the versioned config, not
  from what "should" be acceptable for this issuer.
- **Orientation only, not legal advice**: GENIUS Act, MiCA, NYDFS, and FATF framings orient
  the control set; the firm's approved, jurisdiction-specific policy governs and takes
  precedence.
