---
name: ransomware-readiness-assessor
description: >-
  Assess an organization's or critical service's ransomware readiness across identity, network
  segmentation, backups, recovery, detection, third parties, exercises, crisis communications,
  and critical-service dependencies. Produces explainable, rule-based gap findings with cited
  evidence (privileged-MFA gaps, unsegmented services, missing or non-immutable backups, stale
  restore tests, detection and dependency-mapping gaps, third-party resilience gaps, overdue
  exercises), staged remediation recommendations, and a suggested review priority. Use when a
  CISO office, operational-resilience, or infrastructure owner asks to assess ransomware
  readiness, run a pre-incident control-gap check, or prepare backup/recovery assurance evidence.
  HARD BOUNDARY: R3 decision support only — it never certifies or attests readiness, accepts risk,
  executes or completes a remediation, files a report, or closes the assessment; every remediation
  is staged for a human control owner to adjudicate and execute.
license: MIT
compatibility: Amazon Quick Desktop; requires CMDB/service-registry, backup/recovery, IAM/PAM, SIEM/SOAR/EDR, vulnerability/cloud-posture, threat-intel, vendor-risk, GRC/exercise, and BCP/crisis-comms MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (security-sensitive)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "CISO / Operational Resilience"
  aws-fsi-primary-user: "CISO office / resilience / infrastructure"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Ransomware Readiness Assessor

## Purpose and outcome
Given a scope (the organization or a critical service) and its control-posture extract, compute
a set of **explainable, rule-based ransomware-readiness gap findings** across the readiness
domains — identity, segmentation, backups, recovery, detection, third parties, exercises,
communications, and critical-service dependencies — attach cited evidence to each, **stage
remediation candidates for approval**, and produce a review-ready pack with a **suggested
remediation-review priority**. A successful output lets a CISO office / operational-resilience
owner adjudicate readiness gaps and plan remediation with consistent evidence — the readiness
decision, the risk acceptance, the remediation, and any attestation or filing remain human.

## Use when
- "Assess our ransomware readiness for the wholesale-payments platform / this critical service."
- "Run a pre-incident control-gap check on backups, recovery, segmentation, and detection."
- "Which critical services lack immutable backups or a recent restore test?"
- "Do our privileged accounts have MFA, and is a ransomware exercise overdue?"
- A control owner needs a cited readiness-gap write-up to attach to a resilience review or
  recertification.

## Do not use
- The user wants to **decide or act** — attest readiness, accept a risk, enforce MFA, re-segment,
  provision backups, file a report, or close the assessment. Out of scope: produce evidence +
  staged candidates and route to the human control owner and the executing teams (see Human approval).
- A **live or suspected ransomware incident** is underway → `cyber-incident-response-coordinator`
  (this skill is pre-incident readiness, not incident response).
- **Grant-level identity detail** (privileged entitlements, SoD, dormant/orphaned accounts) →
  `identity-access-reviewer`.
- A **cloud misconfiguration** (over-broad policy, missing logging/encryption) rather than a
  service-level control gap → `cloud-security-posture-reviewer`.
- **Vulnerability/exposure prioritization** on the critical assets → `vulnerability-prioritization-assistant`.
- **Critical-third-party** security/resilience assurance in depth → `third-party-cyber-risk-reviewer`.
- **Exercise design** or **regulatory resilience reporting** → `operational-resilience-scenario-tester`
  / `operational-resilience-reporter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a readiness assessment with
a durable `readiness_id`; downstream review/investigation/reporting skills consume it. Remediation
execution, readiness attestation, risk acceptance, and regulatory filing are authorized
human/operations/governance actions outside this skill — there is no catalog skill that executes
writes. It must not duplicate a downstream skill's decision or action steps.

## Inputs and prerequisites
- The **scope** (organization unit or critical service) and an `as_of` date.
- A **posture extract**: `critical_services` (service_id, tier, `segmented`, `backup`
  {exists, immutable, offline_copy}, `last_restore_test`, `detection_coverage`, `dependency_map`,
  source_ref); optional `identity` (privileged counts, MFA, tiering), `third_parties`,
  `exercises`, and `communications` blocks, each with a `source_ref`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The versioned **readiness config**: restore-test / exercise / comms-test intervals, minimum
  detection coverage, minimum privileged-MFA ratio, relevant exercise types (see
  [references/domain-rules.md](references/domain-rules.md)); record its `config_version`.
- Read access to CMDB, backup/recovery, IAM/PAM, SIEM/EDR, vendor-risk, GRC, and BCP systems.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The CMDB critical-service record is the
position of record for what is in scope; the backup/recovery platform is the position of record
for backup and restore-test state. When an asserted control conflicts with the platform of record
(e.g. "backups are immutable" vs. the backup platform), that conflict IS the finding — cite both,
never resolve it silently.

## Workflow
1. **Scope & validate** — confirm the scope, `as_of`, and config version; load the extract and
   validate it with `validate_input` (fails closed on structure; warns on data gaps that limit
   which gaps are evaluable).
2. **Compute findings (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   configured control gaps. Each fired gap returns its evidence rows with citations. Gaps are
   **explainable rules**, not a black-box score; unevaluable gaps are reported as `not_evaluable`.
   Absence of positive control evidence is treated conservatively as a gap (see domain-rules).
3. **Stage remediation candidates** — for actionable/escalator gaps the engine stages remediation
   **candidates** (`status: staged_for_approval`), deduplicated by `{finding}:{target}`, each tied
   to the fired finding. These are recommendations for a human, never executed changes.
4. **Suggest priority** — map the fired-gap profile to a review-priority band (Informational /
   Review / Elevated) per the documented deterministic mapping. This is a triage suggestion for a
   control owner, explicitly **not** a readiness decision, rating, or attestation.
5. **Write the pack** — plain-language explanation per gap + cited evidence + staged candidates +
   suggested priority + review-context prompts to weigh before adjudicating.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: every fired finding has evidence + citation; the priority maps
deterministically from the fired set; **no readiness-decision / attestation / risk-acceptance /
remediation-execution / filing / closure language** is present; every staged remediation is a
candidate tied to a fired finding (an executed status fails closed); the standing disclaimer is
present; and context prompts are included. Fail closed on any miss.

## Human approval
`required` (R3): a human control owner (CISO office / operational resilience) must **adjudicate
every finding and approve every staged remediation** before any change, and the readiness
attestation, risk acceptance, and any regulatory filing are theirs. The skill never certifies or
attests readiness, never accepts risk, never executes a remediation, never files a report, and
never closes the assessment or writes a system of record. Approved remediations are executed by
the engineering/infrastructure teams through change management, outside this skill.

## Failure handling
- **Missing control evidence** (`segmented`, `backup`, `dependency_map`, `last_restore_test`
  absent) → treated conservatively as the corresponding gap; never assumed compliant.
- **Missing measured value** (`detection_coverage` absent) → reported as `not_evaluable` for that
  row; never inferred.
- **No `identity` / `third_parties` / `exercises` / `communications` block** → the dependent gaps
  are reported as `not_evaluable`, not silently skipped.
- **Ambiguous scope / service identity** → stop and confirm; never assess the wrong scope or map a
  control to the wrong service.
- **Asserted-control vs. platform-of-record conflict** → surface it as the finding with both
  citations; do not resolve.
- **Stale / missing config version** → do not guess thresholds; record the version used and flag
  if unknown.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag; page large
  scopes as resumable stages.

## Output contract
1. **Summary** — scope, `as_of`, config version, count of fired gaps, suggested priority.
2. **Findings** — per fired gap: name, domain, plain-language reason, criteria, evidence rows
   (cited), and the threshold/rule it breached.
3. **Staged remediation candidates** — target, related finding, action, `status:
   staged_for_approval` (for approval; not executed).
4. **Review-context prompts** — exceptions to weigh (compensating control, remediation in flight,
   planned decommission, out-of-band vault, unlogged exercise).
5. **Not-evaluable gaps** and data gaps.
6. **Machine-readable** — findings + evidence + staged candidates + `readiness_id` for downstream.
7. **Standing disclaimer** — "Ransomware-readiness assessment: evidence and staged remediation
   recommendations only; not a readiness decision or attestation. No remediation has been executed
   and no assessment has been filed or closed."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential, security-sensitive. Minimize output to the services/controls that evidence a fired
gap. Do not disclose exploitable detail (exact host inventories, credentials, live configuration)
beyond what evidences the gap. Retain the assessment + citations + `config_version` per records
policy; log the read and any control-owner approval of staged remediations. Never exfiltrate
control-posture data.

## Gotchas
- **A gap is not a decision.** Findings justify *review priority* and a *staged candidate*, never a
  readiness attestation, a risk acceptance, or a remediation.
- **Absence of evidence is a gap, not a pass.** Readiness fails safe toward the defender: a missing
  backup, missing segmentation flag, or missing restore-test date fires the gap — an unproven
  control is exactly the ransomware risk.
- **Immutable *or* offline.** A backup that exists but is neither immutable nor air-gapped is still
  reachable by an attacker with domain privileges; that is the immutability gap, distinct from
  having no backup at all.
- **Restore test ≠ backup existence.** A backup you have never restored is unproven recovery; the
  recovery gap is separate from the backup gap.
- **Readiness is point-in-time.** The assessment reflects the `as_of` extract; a remediation in
  flight may not yet show — the context prompts exist so the owner weighs this before prioritizing.
- **Config is a versioned contract.** Intervals and thresholds come from the approved config, never
  tuned to make a given scope look ready.
- **Describe, don't accuse or predict.** State a gap as a control exception with evidence; do not
  assert negligence or predict that a ransomware event will occur.
