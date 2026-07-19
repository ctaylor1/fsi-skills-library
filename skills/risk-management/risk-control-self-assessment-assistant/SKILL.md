---
name: risk-control-self-assessment-assistant
description: >-
  Prepare and challenge a first-line Risk & Control Self-Assessment (RCSA): score inherent
  risk from impact and likelihood, derive control design and operating effectiveness, compute
  residual risk against appetite, map every credited control conclusion to evidence, surface
  statement and control challenges, and draft a remediation plan — assembled into a controlled
  RCSA package template. Use when a first-line risk or operational-risk analyst needs to build,
  refresh, or challenge an RCSA, map control evidence, score design and operating
  effectiveness, or track remediation for operational, compliance, or third-party risks.
  Draft-only decision support: it NEVER signs off, attests, self-certifies, closes, finalizes,
  accepts risk, or writes the GRC system of record, and NEVER credits a control without
  evidence — control-owner attestation, first-line sign-off, and independent second-line
  challenge are mandatory before an RCSA becomes a record.
license: MIT
compatibility: Amazon Quick Desktop; requires GRC/risk-register, controlled-content (ERM/RCSA standard + appetite), control-testing/assurance, loss-event, KRI, third-party-inventory, and finance/operational MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Risk Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "First-line risk / operational-risk analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Risk & Control Self-Assessment Assistant

## Purpose and outcome
Help a first-line risk analyst produce a **defensible, evidence-mapped RCSA draft**: score
inherent risk, assess control design and operating effectiveness, compute residual risk
against appetite, challenge the risk/control statements, and draft a remediation plan —
assembled into the controlled RCSA template
([assets/output-template.md](assets/output-template.md)). The output is a **draft package**
that a control owner, first-line management, and the independent second line review, sign
off, and (only they) commit to the GRC system of record. The value is a faster, more
consistent, better-evidenced assessment — never a self-certified control opinion.

## Use when
- "Help me prepare / refresh the RCSA for this process or business unit."
- "Score these risks and controls (inherent, design/operating effectiveness, residual)."
- "Challenge my risk and control statements — where are the gaps or unsupported ratings?"
- "Map the evidence to each control conclusion / find the evidence gaps."
- "Draft the remediation plan for residual risks above appetite and track their status."

## Do not use
- **Top-down / enterprise risk assessment** aggregation → `enterprise-risk-assessment-builder`.
- **Investigating a live loss event / near-miss** → `operational-risk-event-analyzer`.
- **Second-line independent challenge or validation** → a human second-line function (this
  skill is first-line drafting support and cannot substitute for it).
- **Signing off, attesting, accepting risk, or writing the GRC system of record** → refuse;
  those are human decisions.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). RCSA is first-line drafting; independent
challenge, sign-off, and GRC finalization are human controls. Loss-event and KRI evidence
feed in; results roll up to the enterprise assessment and risk-committee packs. The draft
carries methodology/appetite versions and evidence citations so downstream consumers do not
re-derive ratings.

## Inputs and prerequisites
- The in-scope entity/process; assessment period and as-of date; **risk appetite**; and the
  risk register rows — each with a statement, category, inherent impact (1–5) and likelihood
  (1–5), mapped controls (design + operating ratings) and their **evidence**, plus any loss
  events / KRIs and optional remediation. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the GRC register, ERM/RCSA standard and appetite (versioned), control-testing
  results, loss events, KRIs, and third-party inventory.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The GRC register is the system of
record; the ERM/RCSA standard and appetite are **versioned contracts**. Every credited
control conclusion cites dated evidence; stale or missing evidence is a challenge, not a
silent credit.

## Workflow
1. **Validate & scope** — run `validate_input`; confirm entity, period, appetite, and that
   each risk has impact/likelihood and controls carry ratings. Flag data gaps.
2. **Score inherent risk (deterministic)** — impact × likelihood → level/band per
   [references/domain-rules.md](references/domain-rules.md).
3. **Assess control effectiveness (evidence-gated)** — combine design + operating into an
   overall rating; **downgrade any crediting conclusion without evidence to `Unsubstantiated`**
   (not credited). Run [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py).
4. **Compute residual & appetite** — reduce inherent by the best mitigating control; compare
   residual to appetite; set `remediation_required` where residual exceeds appetite or **any**
   mapped control is ineffective (evaluated independently of best-control selection, so an
   ineffective control is never masked by an earlier zero-reduction control).
5. **Challenge** — surface uncontrolled material risks, evidence gaps, and loss-event/KRI
   contradictions for the reviewer. These are prompts, not conclusions.
6. **Draft remediation** — for each triggered risk, a remediation item with owner/due date
   (flag `TBD` where absent) and an aging status.
7. **Assemble package** — populate the RCSA template with the required-approvals block set to
   `pending`. Draft-only; never sign off or write back.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: all required template sections present; **no unsupported
assertions** (credited control conclusions carry evidence); residual ties out to the
deterministic mapping; **required approvals recorded** (control owner, first-line sign-off,
second-line challenge — none marked obtained without a named approver+date); no autonomous
sign-off/attestation/closure/filing/risk-acceptance language; standing note present. **Fail
closed** on any miss.

## Human approval
`required`. This skill drafts and packages; humans decide. Control-owner attestation of
accuracy, first-line management sign-off, and **independent second-line challenge/validation**
are mandatory before the RCSA is a record. Remediation acceptance, waiver, and any
risk-acceptance above appetite belong to the accountable risk owner or risk committee. Writing
the RCSA to the GRC system of record is a human action via the GRC platform.

## Failure handling
- **Missing impact/likelihood or ratings** → `validate_input` errors; do not guess a score.
- **Rated control with no evidence** → mark `Unsubstantiated`, do not credit, raise a
  challenge and a `needs` item; never assert an unevidenced control benefit.
- **No controls on a material risk** → residual equals inherent; challenge as uncontrolled.
- **Stale/conflicting evidence** → cite it and flag for the reviewer; do not silently credit.
- **Loss event vs. Effective rating** → challenge and require corroboration before sign-off.
- **Tool timeout / partial data** → return a partial draft with an explicit incomplete flag;
  assume no retry and no step-up authorization.

## Output contract
1. **RCSA draft package** ([assets/output-template.md](assets/output-template.md)) with:
   assessment scope; per-risk inherent/controls/residual assessment; residual summary;
   evidence map; challenges & gaps; remediation plan; required-approvals block (`pending`).
2. **Machine-readable** — the scored package JSON keyed by `risk_id` (see the transform).
3. **Challenges list** — the reviewer's action items (gaps, uncontrolled risks, contradictions).
4. **Standing note** — "DRAFT RCSA for human review only; no assessment has been signed off,
   challenged, attested, risk-accepted, or written to the GRC system of record by this
   assistant." See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Mask personal identifiers; RCSA content is internal control information.
Retain the draft, its evidence citations, and the methodology/appetite versions alongside the
final GRC record per retention policy; log the preparer identity and every source read. The
draft is **not a record** until human sign-off is captured in the GRC system.

## Gotchas
- **Self-assessment ≠ self-certification.** The skill drafts a first-line view; it never
  attests or signs off, and it cannot replace the independent second-line challenge.
- **Evidence gates credit.** A control rated Effective with no evidence is `Unsubstantiated`
  and earns **no** residual reduction — overstating the control environment is the primary R3
  failure mode.
- **Residual is computed, not decided.** The residual band and remediation triggers are
  deterministic inputs to a human decision, not a risk-acceptance.
- **Remediation is flagged, not closed.** The assistant ages items and flags `TBD` owners; it
  never closes, waives, or accepts them.
- **Methodology & appetite are versioned.** Record the version on every package so the scoring
  is reproducible and reviewable.
