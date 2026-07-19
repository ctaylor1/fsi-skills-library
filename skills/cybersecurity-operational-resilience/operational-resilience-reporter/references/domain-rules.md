# Domain Rules — operational-resilience-reporter

Orientation references: UK PRA/FCA operational-resilience policy (important business
services, impact tolerances, mapping, scenario testing, self-assessment), EU DORA (ICT
third-party register, major ICT-incident classification/reporting, threat-led testing), and
US interagency sound practices for operational resilience. The firm's resilience framework
and its **jurisdictional rule pack + report templates** take precedence and are versioned
contracts. These are orientation only — this skill drafts reports; it makes no regulatory
determination and files nothing.

## Report types and required sections (deterministic)

Required sections are configuration, not judgment. The base template per `report_type` plus
the `jurisdiction` pack define the section set; both are overridable via the input `ruleset`
(a versioned contract). `validate_output` enforces that every required section is present.

| report_type | Base required sections (before jurisdiction pack) |
| ----------- | -------------------------------------------------- |
| `incident` | executive-summary, incident-chronology, impacted-important-business-services, impact-tolerance-assessment, root-cause-and-remediation, customer-and-market-impact, regulatory-notification-status, approvals |
| `impact-tolerance` | executive-summary, important-business-services, impact-tolerance-statements, mapping-and-third-parties, vulnerabilities-and-remediation, remediation-plan, approvals |
| `dependency` | executive-summary, service-dependency-map, critical-third-parties, concentration-and-substitutability, exit-and-contingency, approvals |
| `testing` | executive-summary, scenario-testing-summary, tolerance-outcomes, vulnerabilities-and-remediation, lessons-learned, approvals |
| `self-assessment` | executive-summary, important-business-services, impact-tolerance-statements, mapping-and-third-parties, scenario-testing-summary, incident-experience, vulnerabilities-and-remediation, lessons-learned, board-attestation-status, approvals |

Jurisdiction packs add sections: **UK-PRA-SS1-21** → `self-assessment-document-reference`;
**EU-DORA** → `ict-third-party-register`, `major-incident-classification`;
**US-INTERAGENCY** → `interconnection-and-concentration`.

## Deterministic facts (computed, explainable — never a determination)

- **Incident duration** = `resolved − (detected | start)`, in minutes.
- **Impact-tolerance breach** = observed metric vs the register threshold, by tolerance
  `direction` (`max`: breach if observed > threshold). This is a *factual observation*, not
  a compliance decision.
- **Register completeness** = required fields present (IBS impact-tolerance threshold;
  critical third-party contract + exit-plan refs). Missing fields are reported, not filled.
- **Third-party concentration** = a critical third party supporting more than one in-scope
  service (flags a substitutability review — does not conclude one).
- **Major-incident classification (DORA)** = severity is passed through as an *input* to the
  human classification; the skill never assigns the final regulatory classification.

## Required approvals (recorded, human)

The package must record an `accountable-executive` approval and a `second-line-review`
approval — each with a name, date, and `approved` decision — before it is review-complete.
These are human decisions the skill *records*; it does not grant them.

## Hard boundaries (fail closed)

- No **regulatory submission/filing** to any supervisor.
- No **attestation/certification** on behalf of a person or the board.
- No **resilience/compliance determination** or **case/matter closure**.
- No **fabricated content** in `gap` sections; no **uncited claim** in `drafted` sections.
- No **overwrite** of register, incident, or test systems of record.

## Draft package — required contents

`report_type`, `jurisdiction`, `template_version`, `ruleset_version`, `as_of_date`; the full
required-section set (each `drafted` with cited facts or `gap` with a needs-input note);
`impact_tolerance_assessments` with tie-outs; `register_completeness`; `gaps`;
`approvals_recorded` (required roles); empty `unsupported_claims`; the draft watermark and
standing note.
