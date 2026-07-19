---
name: cloud-security-posture-reviewer
description: >-
  Review a de-identified cloud security posture export — configurations, identity/IAM,
  network exposure, logging, encryption, data exposure, and policy violations — and produce a
  source-linked findings pack with cited evidence, recommended remediation, and a deterministic
  remediation-priority disposition. Use when a cloud-security engineer, platform/DevOps
  engineer, or SOC analyst asks to "review our cloud security posture", "what's misconfigured",
  "is this bucket / security group / role exposed", "which findings are critical", or needs
  review-ready evidence before remediation. HARD BOUNDARY: this skill produces findings,
  evidence, and remediation recommendations for a human owner only — it NEVER makes a
  compliance attestation, accepts risk, closes/suppresses/waives a finding, grants an
  exception, applies or deploys a remediation, changes any cloud configuration, or writes a
  system of record; those are human, authorized actions.
license: MIT
compatibility: Amazon Quick Desktop; requires cloud-posture/CSPM, IAM, SIEM/SOAR, CMDB, threat-intelligence, and approved-calculation MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Cloud-security / platform engineering"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Cloud Security Posture Reviewer

## Purpose and outcome
Given a de-identified cloud posture export — resources with their identity, network,
encryption, logging, data-exposure, and tagging/region attributes — run a fixed set of
**documented policy checks**, attach cited evidence to every finding, propose a **recommended
remediation** per finding, and map the finding set to a **remediation-priority disposition**.
A successful output lets a cloud-security or platform engineer see, at a glance, what is
misconfigured, how severe it is, what evidence supports it, and what to do next — while the
decisions to **remediate, accept risk, grant an exception, or attest compliance remain human**.

## Use when
- "Review our cloud security posture / which findings are critical?"
- "Is this bucket / security group / IAM role / database exposed?"
- "What's misconfigured across identity, network, encryption, logging, or data exposure?"
- "Give me cited evidence and a remediation recommendation before I fix or waive anything."
- An engineer needs a consistent, cited posture write-up to attach to a change or ticket.

## Do not use
- The user wants a **compliance attestation**, a **risk acceptance**, a finding **closed /
  suppressed / waived**, an **exception granted**, a **remediation applied**, or any **cloud
  configuration change** → out of scope. Produce findings + evidence + recommendations and
  route the decision/action to the human owner.
- **Deep IAM entitlement / privileged-access / certification review** (staging revocations) →
  `identity-access-reviewer`.
- **Vulnerability (CVE) prioritization** using exploitability, exposure, and threat intel →
  `vulnerability-prioritization-assistant`.
- **Live alert/detection triage and enrichment** → `security-alert-triage-assistant`.
- **Suspected data exfiltration / DLP incident** investigation → `data-loss-prevention-incident-assistant`.
- **Active-compromise incident** coordination → `cyber-incident-response-coordinator`.
- The posture belongs to a **third party/supplier** → `third-party-cyber-risk-reviewer`.
- **Regulatory resilience reporting** from registers → `operational-resilience-reporter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a review pack with a
durable `review_id`; downstream identity, vulnerability, DLP, and incident skills consume it.
It must not duplicate their investigation, drafting, or any remediation/attestation.

## Inputs and prerequisites
- **Assessment identifier** and the posture export: `assessment_id`, `as_of` (YYYY-MM-DD),
  `config_version`, `cloud_provider`, `scope{account_ids[], environment}`, and `resources[]`
  where each resource carries `resource_id`, `type`, `region`, `criticality`, `source_ref`,
  and the type-specific attributes the checks read (e.g. `mfa_enabled`, `ingress[]`,
  `encrypted`, `public_access`, `logging_enabled`, `tags`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the CSPM/config export, IAM, CMDB (criticality/data classification), and the
  versioned **policy config** (thresholds, port sets, allowed regions, required tags — see
  [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The CSPM/config export is the
position of record for resource state; IAM governs identity; CMDB supplies criticality and
data classification; config supplies thresholds and policy sets. Cite every finding to a
resource record and the config rule. On conflict (export vs a claimed compensating control),
cite both and raise a finding — never resolve it as a posture conclusion.

## Workflow
1. **Scope & load** — confirm the account scope and `as_of`; load the export; validate with
   `validate_input`. Fail closed on structural problems.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   identity, network, encryption, data-exposure, logging, and policy checks. Each fired check
   returns a severity, cited evidence, and a recommended remediation. Checks are
   **explainable**, not a black-box score; unreadable attributes are reported `not_evaluable`.
3. **Map disposition** — map the finding set to `remediate_now` / `remediation_required` /
   `review_recommended` / `posture_acceptable` per the deterministic mapping. This is a triage
   suggestion for a human, explicitly **not** a compliance attestation or a risk decision.
4. **Write the pack** — per-finding evidence + recommended remediation + disposition +
   reviewer considerations + recommended handoffs, with the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen confirms: every finding has cited evidence, no
attestation/closure/exception/remediation-execution language is present, the disposition maps
deterministically from finding severities, the disclaimer is present, and reviewer
considerations are included. Fail closed on any miss.

## Human approval
`required`: a cloud/platform owner, security control owner, or CISO/GRC delegate must
adjudicate before any remediation is applied, any finding is closed/suppressed/waived, any
exception or risk acceptance is granted, any compliance attestation is made, or the review is
written into a system of record. No approval is needed for the engineer's own read. The skill
never changes a cloud configuration or a system of record.

## Failure handling
- **Missing attribute** (e.g. no `encrypted`, no `ingress`) → report the check `not_evaluable`;
  never infer a pass or a fail from absent data.
- **Ambiguous scope/account** → stop and confirm; never review the wrong account.
- **Missing criticality / data classification** → warn that severity may be understated; do not
  guess a classification to reach a disposition.
- **Stale/conflicting sources** (export vs claimed compensating control) → cite both; raise a
  finding rather than resolving it silently.
- **Tool timeout** → return the checks completed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — assessment (masked scope), `as_of`, cloud provider, resource count, findings
   by severity, posture disposition.
2. **Findings** — per finding: id, category, severity, rule, resource, plain-language summary,
   cited evidence, recommended remediation.
3. **Not evaluable** — checks skipped for missing attributes, with the reason.
4. **Reviewer considerations** — compensating-control, labelling, and framework cautions the
   human must weigh before acting.
5. **Recommended handoffs** — adjacent skills for deeper identity, vulnerability, DLP, or
   incident work.
6. **Machine-readable** — findings + evidence + `review_id` + `config_version` for downstream
   skills and reproducibility.
7. **Standing disclaimer** — "Posture findings and remediation evidence only; not a compliance
   attestation or risk-acceptance decision. No finding closure, suppression, waiver, or risk
   acceptance has been made, no exception has been granted, and no cloud configuration change
   or remediation has been applied."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential (security-sensitive). A posture export reveals exploitable weaknesses; minimize
to what evidences a finding, mask account identifiers where surfaced, and never include live
secrets, keys, or tokens in the pack. Retain the review + citations + `config_version` per
records policy; log the read and any approval to write the review into a case. Never exfiltrate
the export or route it to a destination the user did not specify.

## Gotchas
- **A finding is not a decision.** Critical findings justify *escalation and human review*,
  never an attestation, a risk acceptance, or an executed remediation.
- **Absent ≠ compliant.** A missing attribute means the check could not run (`not_evaluable`),
  not that the resource passed. Never treat silence as a pass.
- **Compensating controls live outside the export.** A world-open port may sit behind a WAF or
  private path; the pack flags the exposure for the owner to confirm, it does not clear it.
- **Severity depends on labels.** Criticality and data-classification labels drive severity;
  a mislabelled bucket understates or overstates a finding — verify the labels.
- **No framework attestation.** Mapping a finding to PCI/SOC 2/FFIEC/NIST is context for the
  human; the skill never states an environment is compliant with any framework.
- **Do not tune config to the environment.** Thresholds, port sets, allowed regions, and
  required tags come from the versioned config, not from what "should" pass here.
