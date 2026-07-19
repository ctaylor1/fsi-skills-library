---
name: enterprise-risk-assessment-builder
description: >-
  Build a controlled DRAFT enterprise (or business-unit) risk assessment that links risks,
  scenarios, controls, residual ratings, indicators, owners, evidence, and treatment actions
  into an approved template, using a deterministic inherent -> control-credit -> residual ->
  appetite mapping. Use when an enterprise risk manager or business risk officer needs to
  assemble or refresh a risk assessment, tie residual ratings to controls and appetite, flag
  over-appetite risks that require treatment, or package it for second-line challenge, audit,
  or a regulatory exam. This skill NEVER accepts a residual rating, approves or finalizes the
  assessment, closes a risk, signs an attestation, or files/writes the risk register. It
  drafts cited evidence and recommendations for mandatory human adjudication (Risk Owner ->
  Enterprise Risk Management -> Risk Committee/CRO), takes control credit ONLY for tested and
  evidenced controls, and fails closed on unsupported assertions.
license: MIT
compatibility: Amazon Quick Desktop; requires risk-register/GRC, control-testing, risk-appetite/limits, KRI, loss-event, scenario, third-party-inventory, and finance/operational-data MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Enterprise risk manager / business risk officer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Enterprise Risk Assessment Builder

## Purpose and outcome
Assemble a controlled **draft** enterprise (or business-unit) risk assessment that links each
risk to its scenarios, controls, residual rating, key risk indicators, owner, evidence, and
treatment actions, rendered into the approved template. The residual rating is computed by a
documented, deterministic mapping (inherent band reduced by *evidenced* control credit, then
compared to risk appetite). The outcome is an audit-ready draft — cited, tie-out-consistent,
with over-appetite risks and evidence gaps surfaced — that a human (Risk Owner, then
Enterprise Risk Management, then Risk Committee/CRO) adjudicates. The skill never makes the
accept/approve/close/file decision.

## Use when
- "Build / refresh our enterprise (or business-unit) risk assessment."
- "Tie these residual ratings back to controls and our risk appetite."
- "Which risks are over appetite and missing a treatment action?"
- "Assemble the risk assessment package for second-line challenge / audit / the exam."
- "Link these risks to their KRIs, loss events, scenarios, and evidence."

## Do not use
- **RCSA control scoring / evidence mapping** → `risk-control-self-assessment-assistant`.
- **KRI monitoring against thresholds** → `key-risk-indicator-monitor`.
- **Loss / near-miss event classification** → `operational-risk-event-analyzer`.
- **Scenario / stress design** → `stress-test-scenario-designer`.
- **Vendor / third-party assessment** → `third-party-risk-assessor`.
- **Concentration monitoring** → `concentration-risk-monitor`.
- Any request to **accept a residual, approve/finalize, close a risk, attest, or file** →
  refuse; route to human adjudication.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is the **assembler**: it
consumes cited component analyses upstream and hands a durable, versioned draft
(`assessment_id`, `template_version`, `config_version`) to human adjudication and, once
approved by humans, to exam/audit packaging. It does not re-run specialist analyses and does
not adjudicate.

## Inputs and prerequisites
- Risk inventory with owners and inherent likelihood/impact; the linked controls with design
  and operating effectiveness and test evidence; the risk-appetite bands per category; KRIs;
  loss events; scenarios; third-party and finance/operational context; and the scoring/
  template versions. Schema and field list: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the risk register/GRC, control-testing, appetite/limits, KRI, loss-event,
  scenario, third-party-inventory, and finance/operational sources (all read-only).
- Data-quality minimum: likelihood/impact are integers 1–5; a control earns residual credit
  only if it is **tested** and carries an **evidence reference**.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The risk register is the system of
record for risk state; control-testing evidences effectiveness; appetite and the scoring
config are versioned contracts. Cite every rating, effectiveness claim, KRI value, loss event,
and scenario. This skill reads only; it never writes the register.

## Workflow
1. **Validate & normalize** — run [scripts/validate_input.py](scripts/validate_input.py);
   fail closed on structural issues; record completeness gaps (untested/unevidenced controls,
   missing owner, missing appetite band) as warnings that drive `needs-evidence`.
2. **Score inherent risk (deterministic)** — likelihood × impact → band (Low/Moderate/High/
   Critical) per [references/domain-rules.md](references/domain-rules.md).
3. **Assess the control environment** — for each risk, take residual credit **only** from
   controls that are tested (proven) **and** evidenced; untested/unevidenced controls earn no
   credit and are flagged. Average credited control strength → control tier → band reduction.
4. **Compute residual & appetite** — residual band = max(Low, inherent − reduction); compare
   to the category appetite; flag every residual **over appetite**. Run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) — explainable
   inputs, not a black box.
5. **Link indicators, evidence, and treatment** — attach KRIs, loss events, scenarios, and
   the evidence register; require a treatment action for every over-appetite residual.
6. **Render the template** — populate every required section of
   [assets/output-template.md](assets/output-template.md); leave all approvals `pending`.
7. **Never decide** — no acceptance, approval, finalization, closure, attestation, or filing.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: all required template sections present; residual bands tie
to the deterministic mapping; over-appetite flag consistent; control credit only where
proven + evidenced (no unsupported assertions); a treatment action for every over-appetite
residual; no decision/closure/filing language; the three required approvals recorded and left
pending; standing note present. Fail closed on any miss and correct before presenting.

## Human approval
`required`. This skill drafts and packages; it decides nothing. Acceptance of a residual
rating, approval/finalization of the assessment, risk closure, attestation sign-off, and any
write to the risk register are **human/committee actions** (Risk Owner → Enterprise Risk
Management (2nd line) → Risk Committee/CRO) via the approval broker, outside this skill.

## Failure handling
- **Untested / unevidenced control** → take no residual credit; flag in Limitations; set the
  risk `needs-evidence`. Do not manufacture reduction.
- **Missing data** (owner, appetite band, likelihood/impact) → surface exactly what is
  missing; do not guess a rating.
- **Over-appetite residual with no treatment** → record the gap; never hide it or downgrade
  the residual to fit appetite.
- **Stale / conflicting sources** → cite both, use the fresher, and flag the conflict.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no
  retry.

## Output contract
1. **Draft assessment** rendered to [assets/output-template.md](assets/output-template.md):
   Scope & Basis; Risk Inventory; Inherent Risk Assessment; Control Environment; Residual Risk
   & Appetite; Key Risk Indicators; Treatment Actions; Evidence Register; Limitations &
   Assumptions; Approvals & Attestations.
2. **Per-risk record** — inherent (L, I, score, band), controls (proven/credited/evidence),
   control tier & reduction, residual band, appetite band, over-appetite flag, linked KRIs/
   scenarios/loss events, treatment actions, evidence refs, citations, gaps, and a draft
   status (`draft-for-review` | `needs-evidence`).
3. **Machine-readable** — the assessment JSON keyed by `assessment_id`, with
   `template_version`/`config_version` and all approvals `pending`.
4. **Standing note** — "Draft enterprise risk assessment for human review only; no risk has
   been accepted, no residual rating approved, no assessment finalized, and nothing filed or
   written to the risk system of record."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Operate on risk/control/indicator metadata, not raw customer records;
minimize identifiers. Retain the draft, its inputs, the scoring/appetite/template versions,
and all citations per the firm's records schedule; log the preparer identity and every source
read. US jurisdiction by default; configure additional packs per deployment.

## Gotchas
- **Draft ≠ decision.** Producing a residual rating is a recommendation; accepting it is a
  human/committee act. The skill leaves approvals pending and uses only draft states.
- **No credit for untested controls.** A control marked *Not Tested* — or tested but without
  an evidence reference — earns zero residual reduction. This is deliberate and fail-closed.
- **Over appetite always needs treatment.** Never downgrade a residual to fit appetite; record
  the gap and the required treatment action.
- **Residual is a mapping, not a judgment.** Residual = inherent − evidenced control credit;
  the config is versioned so the result is reproducible.
- **Cite everything.** An effectiveness claim or KRI value without a source is an unsupported
  assertion and fails the output screen.
- **Legitimate control names are not decisions.** A control titled "Board-approved limits" is
  evidence, not an approval of the assessment; only decision *verbs* are prohibited.
