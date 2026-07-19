---
name: third-party-cyber-risk-reviewer
description: >-
  Review a supplier's cyber-security evidence — control questionnaires (SIG/CAIQ), SOC 2 /
  ISO 27001 attestations, open vulnerabilities, incidents affecting our data, fourth-party
  subcontractors, data access, resilience/BCP, contractual security obligations, and
  remediation — surface findings with cited evidence, and suggest a residual-risk tier for
  human adjudication. Use when a third-party-risk analyst or procurement partner asks
  "review this vendor's security posture", "what are the cyber gaps for this supplier",
  "is this supplier's SOC 2 sufficient", or needs a review-ready evidence pack before an
  onboarding or renewal decision. This skill produces findings, cited evidence, and a
  suggested tier ONLY; it NEVER approves, rejects, onboards, clears, or risk-accepts a
  supplier, closes/signs off an assessment, files/attests, or writes a GRC/TPRM system of
  record — those are human risk-owner decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires vulnerability/cloud-posture, incident/BCP, CMDB, IAM, supplier-evidence, threat-intel, and versioned-config MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Third-party cyber risk / procurement"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Third-Party Cyber Risk Reviewer

## Purpose and outcome
Given a supplier assessment intake (security questionnaire, attestations, vulnerability and
incident posture, subcontractor list, contract terms, resilience evidence, remediation
status), compute a set of **explainable cyber-risk findings**, explain in plain language why
each fired, attach cited evidence to each, and map the fired-finding profile to a **suggested
residual-risk tier**. A successful output lets a third-party-risk analyst or procurement
partner see exactly where a supplier's security posture is weak and hand a review-ready,
evidenced pack to the **human risk owner who adjudicates** onboarding, renewal, or risk
acceptance. The decision — and any register write — remains human.

## Use when
- "Review this vendor's security posture / cyber risk before we onboard or renew."
- "What are the security gaps for supplier X, with the evidence?"
- "Is this supplier's SOC 2 / ISO 27001 sufficient and in scope for the service?"
- "Does this supplier have open critical vulnerabilities or an unresolved incident affecting
  our data?"
- A risk owner needs a consistent, cited cyber-risk write-up to attach to a TPRM case.

## Do not use
- The user wants a **supplier decision** ("approve / reject / onboard this vendor", "accept
  the risk", "grant the exception", "close the assessment") → out of scope. Provide findings
  and route to the human risk owner / GRC-TPRM system of record.
- **Enterprise-wide TPRM** beyond cyber (financial, operational, reputational) →
  `third-party-risk-assessor`.
- **AI/ML supplier** due diligence (model, data, prompt/agent risk) →
  `third-party-ai-due-diligence-assistant`.
- An **active supplier incident** needing coordinated response →
  `cyber-incident-response-coordinator`.
- **Supplier concentration / substitutability** analysis → `concentration-risk-monitor`;
  **resilience impact testing** → `operational-resilience-scenario-tester`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a review with a durable
`review_id`; downstream TPRM, AI-diligence, incident, and resilience skills consume it. It
must not duplicate their scope or reach an adjudication.

## Inputs and prerequisites
- Supplier reference (de-identified) and the **engagement context**: data classification,
  business criticality, whether it hosts regulated data, internet exposure.
- **Security evidence** for the sections to be reviewed: controls (with status + evidence
  ref), certifications (type, `valid_until`, scope), vulnerabilities (open counts, SLA,
  oldest-open age), incidents (severity, occurred/disclosed dates, resolved, affected-our-data),
  subcontractors, contract terms, resilience/BCP, remediation commitments. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the systems in [references/source-map.md](references/source-map.md); the
  approved thresholds/config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Internal systems of record
(vulnerability/cloud posture, incident/BCP, CMDB, IAM) outrank the supplier's own
attestations. Where an internal record contradicts an attestation, cite both and flag the
conflict — never resolve it in the supplier's favor. Cite every finding's evidence to a
source row with its effective date.

## Workflow
1. **Scope & validate** — confirm the supplier, service, and engagement context; load the
   evidence sections; validate with `validate_input`. Note data-quality gaps (unknown-status
   controls, missing evidence refs) that limit evaluability.
2. **Compute findings (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   configured findings (control gaps, stale/missing attestation, open critical
   vulnerabilities, unresolved/late-disclosed incidents, fourth-party data exposure,
   contractual gaps, resilience gaps, overdue remediation). Each finding returns a severity
   and the evidence rows behind it. Findings are **explainable**, not a black-box score.
3. **Assemble evidence** — for each fired finding, attach the specific rows and the threshold
   it breaches, with citations; list `unknown`-status items as `not_evaluable`.
4. **Suggest residual tier** — map the fired-finding profile (top severity, count, engagement
   amplifier) to a residual-risk band (Low / Moderate / High / Critical) per the documented
   deterministic mapping. This is a triage suggestion for a human risk owner, explicitly
   **not** a supplier decision.
5. **Write the review** — plain-language explanation per finding + the evidence + the
   suggested tier + considerations (compensating controls, attestation scope, concentration)
   the risk owner must weigh before adjudicating.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check is the R3 **prohibited-decision screen**: it confirms every fired
finding has cited evidence, the tier ties out to the deterministic mapping and is an allowed
value, **no supplier-decision / risk-acceptance / closure / sign-off / filing language** is
present, the standing disclaimer is included, and considerations are present when findings
fired. Fail closed on any miss.

## Human approval
`required`: a human risk owner must adjudicate before any supplier decision, risk acceptance,
onboarding/renewal, exception, filing/attestation, or GRC/TPRM system-of-record write. No
approval is needed for the analyst's own read of the review. The skill never makes the
decision and never writes a register.

## Failure handling
- **Insufficient evidence** (thin/empty sections) → state which findings are `not_evaluable`;
  do not infer a posture the data does not support; keep the tier low-confidence.
- **Ambiguous supplier/service identity** → stop and confirm; never review the wrong supplier
  or map to the wrong service.
- **Unknown control status** → list as `not_evaluable`; never treat as pass or fail.
- **Attestation vs. internal record conflict** → cite both; do not resolve silently.
- **Stale evidence** (old scan / expired attestation) → flag as stale; do not trust it.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — supplier (de-identified), service, as-of, count of fired findings, suggested
   residual tier.
2. **Findings** — per fired finding: id, plain-language reason, severity, evidence rows
   (cited), and the threshold it breaches.
3. **Not evaluable** — items lacking evidence (e.g., unknown-status controls, missing blocks).
4. **Considerations** — compensating controls, attestation scope/exceptions, concentration,
   classification currency — so the risk owner weighs context before adjudicating.
5. **Machine-readable** — findings + evidence + `review_id` + `config_version` for downstream
   skills.
6. **Standing disclaimer** — "Findings and evidence only; not a supplier approval, risk
   acceptance, or onboarding decision. A human risk owner must adjudicate. No system of record
   has been updated."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential (security-sensitive). Minimize supplier posture data to what evidences a fired
finding; de-identify supplier identifiers in shared artifacts where the deployment requires
it. Retain the review + citations + `config_version` per records policy; log the read and the
downstream human adjudication. Never exfiltrate supplier security detail.

## Gotchas
- **A finding is not a decision.** A Critical tier justifies *urgent human adjudication*,
  never an autonomous approval, rejection, or risk acceptance.
- **Attestation ≠ coverage.** A SOC 2 that is expired, out-of-scope for the service, or full
  of exceptions is not assurance — it reads as missing coverage, not pass.
- **Fourth parties carry the data risk.** A subcontractor processing our data in an
  unapproved region is exposure even if the prime supplier looks clean.
- **Disclosure timeliness matters.** An incident affecting our data disclosed weeks late is a
  finding in its own right, separate from whether it was resolved.
- **Don't tune to the supplier.** Thresholds and the tier mapping come from the versioned
  config, not from what "feels right" for a favored vendor.
