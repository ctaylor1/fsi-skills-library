---
name: operational-resilience-scenario-tester
description: >-
  Design and document severe-but-plausible operational-resilience scenario tests for
  important business services: map people/process/technology/facilities/third-party/data
  dependencies, test observed recovery against each service's impact tolerance (downtime and
  data loss), and assemble the response decisions, recovery evidence, lessons, and a suggested
  review disposition. Use when an operational-resilience or business-continuity team asks to
  design a severe-but-plausible scenario, run a scenario or impact-tolerance test, check
  dependency coverage, or evidence recovery from an exercise. HARD BOUNDARY: read-only decision
  support — it never concludes the firm is compliant or resilient, never signs off a
  self-assessment, attests, files or submits a regulatory report, updates a register, or closes
  a case/exercise; those require human adjudication, and regulatory reporting and jurisdictional
  registers route to operational-resilience-reporter.
license: MIT
compatibility: Amazon Quick Desktop; requires service-register/impact-tolerance, CMDB/dependency-map, incident/BCP, SIEM-SOAR, IAM, vulnerability/cloud-posture, threat-intelligence, and approved-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (security-sensitive)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "CISO / Operational Resilience"
  aws-fsi-primary-user: "Operational resilience / business continuity"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Operational Resilience Scenario Tester

## Purpose and outcome
Given a firm's **important business services (IBS)**, their **impact tolerances**, and their
mapped dependencies, run a multi-step procedure that designs or ingests **severe-but-plausible
scenarios**, tests **observed recovery against the impact tolerance** for each service, checks
**dependency coverage**, and assembles the **response decisions, recovery evidence, lessons,
and a suggested review disposition**. A successful output gives an operational-resilience owner
a reproducible, cited test pack to adjudicate — the resilience conclusion, self-assessment
sign-off, any regulatory filing, and case closure remain human.

## Use when
- "Design a severe-but-plausible cyber scenario to test our payments service against its
  impact tolerance."
- "Run an operational resilience scenario test and record the recovery evidence and lessons."
- "Does this exercise stay within our impact tolerance? What's the recovery margin?"
- "Which dependency dimensions did our scenarios actually exercise — where are the coverage
  gaps?"
- An owner needs a consistent, evidenced scenario-test pack for a resilience self-assessment
  cycle (as input to a human adjudication, not the sign-off itself).

## Do not use
- The user wants a **resilience determination / self-assessment sign-off / board or SMF
  attestation**, or a statement that the firm **is compliant / resilient** → out of scope;
  produce evidence and route to the human adjudicator.
- **Regulatory resilience reporting**, jurisdiction-specific templates, or **critical-service /
  critical-third-party register** updates → `operational-resilience-reporter`.
- A **real, live incident** needing coordination (chronology, roles, containment,
  communications) → `cyber-incident-response-coordinator`.
- **Actual customer remediation** for a real outage → `service-recovery-assistant`.
- **Financial / capital stress testing** (transmission channels, reverse-stress thresholds) →
  `stress-test-scenario-designer` (Risk Management — a different discipline).
- Deep **ransomware readiness** or **third-party supplier** assessments →
  `ransomware-readiness-assessor` / `third-party-cyber-risk-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a scenario-test pack
with a durable `test_id`; downstream reporting, incident, recovery, and readiness skills
consume it. It must not duplicate their reporting, coordination, or closure steps.

## Inputs and prerequisites
- The **important business services** in scope, each with its effective **impact tolerance**
  (`max_downtime_hours`, `max_data_loss_hours`) and its **mapped dependencies** across
  people / process / technology / facilities / third_parties / data.
- One or more **scenarios** per service: threat type, severity, plausibility, narrative,
  dimensions exercised, and the **observed** recovery metrics from the exercise.
- **Decisions, recovery evidence, and lessons** captured during the exercise (each cited).
- The versioned rubric/threshold **config** (`config_version`). Schema and evaluability
  rules: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the register, CMDB, incident/BCP systems, and telemetry (see
  [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The IBS register + impact-tolerance
standard is the position of record; the CMDB provides dependencies; incident/BCP systems and
telemetry provide decisions and observed recovery. The versioned config supplies the rubric
and disposition thresholds. Cite every decision and recovery-evidence row to a source
artifact; where sources conflict, cite each and flag the gap.

## Workflow
1. **Scope & load** — confirm the IBS in scope, their impact tolerances effective at `as_of`,
   and their dependency maps; load the scenarios and exercise records; validate with
   `validate_input` (structural errors fail closed; evaluability gaps warn).
2. **Score scenarios (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). For each scenario
   it applies the severe-but-plausible rubric flags, runs the impact-tolerance test
   (within / breach / not_evaluable with margin) for downtime and data loss, measures
   dependency coverage, checks decision-evidence completeness, and confirms recovery evidence.
3. **Assemble evidence** — attach the cited decisions and recovery artifacts to each scenario;
   surface coverage gaps, rubric flags, and any unevidenced recovery.
4. **Suggest disposition** — map the scenario set to Informational / Review / Escalate per the
   deterministic, documented mapping in [references/domain-rules.md](references/domain-rules.md).
   This is a triage suggestion for a human, explicitly **not** a resilience determination.
5. **Write the pack** — plain-language summary per scenario (observed vs tolerance, coverage,
   decisions, lessons) + the suggested disposition + remediation actions (owned, open for
   human adjudication) + explicit gaps and uncertainties.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every evaluable scenario has recovery evidence and cited
evidence; every response decision is complete; the disposition equals the deterministic
mapping; no prohibited conclusion/sign-off/filing/closure language is present; the standing
disclaimer is present; and remediation actions accompany any breach or high-severity lesson.
Fail closed on any miss.

## Human approval
`required` (R3): a human adjudicator (accountable resilience owner / SMF) must review before
any resilience conclusion, self-assessment sign-off, attestation, regulatory filing, register
update, case closure, or system-of-record change. No approval is needed for the owner's own
read of the pack. The skill never signs off, files, or closes.

## Failure handling
- **Missing observed recovery metric** → scenario `outcome = not_evaluable`; do not infer a
  pass; list it under `not_evaluable`.
- **Ambiguous service/tolerance** → stop and confirm; never test against the wrong tolerance
  or an out-of-date one (use the value in force at `as_of`).
- **Unmapped dependencies** → coverage is measured only against declared dimensions; flag the
  unmapped dimensions as a data gap.
- **Unevidenced recovery or incomplete decisions** → fail closed in `validate_output`; do not
  present the pack as complete.
- **Stale/conflicting sources** → cite each; do not resolve silently.
- **Tool timeout** → return the scenarios scored so far with a clear "incomplete" flag; split
  long programmes into resumable per-service stages.

## Output contract
1. **Summary** — programme, `as_of`, `config_version`, count of scenarios, breaches, and the
   suggested disposition band.
2. **Per scenario** — service, threat type, severity/plausibility (+ rubric flags), the
   impact-tolerance test (observed vs tolerance, outcome, margin), dependency coverage
   (exercised / missing), decisions (cited, complete), recovery evidence (cited), and lessons.
3. **Remediation actions** — one per lesson, with an owner role and status
   `open_for_human_adjudication`.
4. **Gaps / not-evaluable** — missing metrics, coverage gaps, unevidenced items.
5. **Machine-readable** — scenarios + evidence + `test_id` for downstream skills.
6. **Standing disclaimer** — "Scenario-test evidence and recommendations only; ... Human
   adjudication required before any decision or submission."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential (security-sensitive). Scenario narratives, dependency maps, and recovery
telemetry can reveal exploitable weaknesses — minimize detail to what evidences a finding.
Retain the test pack + citations + `config_version` per records policy; log the read and the
human adjudication decision. Never exfiltrate dependency or vulnerability detail.

## Gotchas
- **A test outcome is not a determination.** "Within tolerance" for one exercise is an
  observed fact, not a statement that the service is resilient or compliant going forward —
  that firm-level conclusion is a human adjudication.
- **Severe-but-plausible means both.** A scenario that is severe but implausible (or plausible
  but mild) is a weak test; the rubric flags it rather than silently accepting it.
- **Coverage is measured against real dependencies.** Exercising only technology while
  people/process/third-party/data dependencies go untested is a coverage gap, even if recovery
  looked fast.
- **Do not tune to pass.** Tolerances and the rubric come from the versioned config; never
  adjust them to convert a breach into a within-tolerance result.
- **Tests are not incidents.** This skill designs and evidences *exercises*; a real incident
  routes to `cyber-incident-response-coordinator` and real customer impact to
  `service-recovery-assistant`.
