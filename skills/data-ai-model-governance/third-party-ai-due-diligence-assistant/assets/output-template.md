# Third-Party AI Due-Diligence Package — DRAFT (for human adjudication)

> Draft third-party AI due-diligence package for human review only; this skill does not
> approve, onboard, or reject any provider, does not accept risk, and does not sign or execute
> any contract. The residual rating and recommended disposition are decision support — a human
> must adjudicate before any onboarding decision.

Fill every `{{placeholder}}` from validated sources. Do not add a finding that is not backed
by a listed evidence item. Do not assert a decision, an approval, or a risk acceptance.

## 1. Engagement identifiers

| Field | Value |
| ----- | ----- |
| Engagement reference | {{engagement_id}} |
| Provider | {{provider_name}} |
| Use case | {{use_case}} |
| Deployment | {{deployment}} |
| Provider criticality | {{criticality}} |
| Rubric version | {{rubric_version}} |
| Assessed as of | {{as_of_date}} |

## 2. Domain coverage

Each required domain for a {{criticality}}-criticality provider, with the freshest supporting
evidence. Uncovered or stale domains block packaging and are listed in section 5.

| Domain | Covers | Evidence present | Freshest evidence (as of) |
| ------ | ------ | ---------------- | ------------------------- |
| {{domain}} | {{domain_label}} | {{evidence_present}} | {{freshest_as_of}} |

## 3. Findings (each cites an evidence item)

Factual and evidence-bound. No finding without a bundled exhibit; no claim beyond what the
evidence shows.

| Finding | Domain | Severity | Statement | Evidence |
| ------- | ------ | -------- | --------- | -------- |
| {{finding_id}} | {{domain}} | {{severity}} | {{statement}} | {{evidence_id}} |

## 4. Residual risk & recommended disposition

| Field | Value |
| ----- | ----- |
| Residual risk score | {{residual_risk_score}} |
| Residual risk rating | {{residual_risk_rating}} |
| Hard gates triggered | {{hard_gates}} |
| **Recommended disposition** (for human adjudication) | {{recommended_disposition}} |

Recommended disposition is one of `proceed-with-conditions`, `remediate-before-onboarding`,
`do-not-proceed`. It is a recommendation, not a decision. `human_adjudication_required: true`.

## 5. Open gaps / conditions

Remediation items, open risk flags, and any blocking reason (missing domain, stale evidence,
unsupported finding). These are the conditions a human weighs before deciding.

- {{open_gap}}

## 6. Reviewer adjudication (required before any onboarding decision)

- [ ] Required domains covered and evidence fresh per the current rubric version.
- [ ] Every finding is supported by a bundled evidence item; no unsupported claims.
- [ ] Residual rating and recommended disposition reviewed; residual risk NOT auto-accepted.
- [ ] Onboarding decision, risk acceptance, and any contract execution performed by the
      accountable authority — not by this skill.

Adjudicator: ________________________  Date: ____________
Decision (human): proceed-with-conditions / remediate / do-not-onboard / request-more-evidence
