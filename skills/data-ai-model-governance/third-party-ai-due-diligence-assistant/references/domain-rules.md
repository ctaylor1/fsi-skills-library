# Domain Rules — third-party-ai-due-diligence-assistant

Third-party AI due-diligence logic applied by
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). All values are a
**versioned contract** (`rubric_version`); the defaults below are illustrative and must be
confirmed against the current AI governance policy at deployment. This reference does not make
onboarding decisions and does not accept risk.

## Due-diligence domains & evidence (default rubric)

A required domain is **covered** when at least one bundled evidence item for that domain
carries an accepted type. `Freshness` is the maximum age of the freshest item.

| Domain | Covers | Accepted evidence types | Freshness |
| ------ | ------ | ----------------------- | --------- |
| provider_profile | Viability & ownership | financials, ownership_disclosure, d&b_report, corporate_profile | 365d |
| model_transparency | Model documentation | model_card, system_card, intended_use_doc, limitations_doc, training_data_provenance | 365d |
| data_governance | Privacy, residency, retention | data_processing_agreement, privacy_assessment, data_residency_attestation, retention_policy | 365d |
| subcontractors_fourth_party | Subprocessors / fourth party | subprocessor_list, fourth_party_disclosure | 365d |
| concentration_risk | Systemic dependency | concentration_analysis, dependency_map, foundation_model_disclosure | 365d |
| security_controls | Security posture | soc2_type2, iso_27001, penetration_test, security_questionnaire | 365d |
| testing_evaluation | Model testing | evaluation_report, bias_fairness_test, red_team_report, benchmark_results | 180d |
| contractual_rights | Contract protections | audit_right_clause, right_to_test_clause, incident_notification_clause, liability_ip_clause, model_change_notification_clause | none |
| resilience_continuity | Continuity | sla, bcp_dr_plan, uptime_report, incident_history | 365d |
| exit_strategy | Exit & portability | exit_plan, data_portability_attestation, transition_support_clause | none |

## Required domains by provider criticality

| Criticality | Required domains |
| ----------- | ---------------- |
| High | all 10 domains |
| Medium | provider_profile, model_transparency, data_governance, security_controls, testing_evaluation, contractual_rights, exit_strategy |
| Low | provider_profile, data_governance, security_controls, contractual_rights |

An unclassified criticality yields `needs-data` (classify the engagement first); it is never
assessed on a guess.

## Residual-risk rubric (deterministic)

Residual score = sum(risk-flag points) + sum(finding-severity points).

| Risk flag | Kind | Points |
| --------- | ---- | ------ |
| data_residency_unapproved | hard gate | 10 |
| no_incident_notification_right | hard gate | 10 |
| no_exit_plan_production | hard gate | 10 |
| unmanaged_concentration | hard gate | 10 |
| training_data_rights_unverified | soft | 6 |
| prior_security_incident | soft | 6 |
| no_bias_testing | soft | 3 |
| subprocessors_undisclosed | soft | 3 |
| no_model_change_notification | soft | 3 |
| sla_below_threshold | soft | 3 |

Finding severity points: `low 1`, `medium 3`, `high 6`, `critical 10`.

**Rating.** Any **hard-gate** flag or any **critical** finding → `Critical`. Else score ≥ 6 →
`High`; ≥ 3 → `Medium`; < 3 → `Low`.

**Rating → recommended disposition** (a recommendation for human adjudication, never a decision):

| Residual rating | Recommended disposition |
| --------------- | ----------------------- |
| Critical | do-not-proceed |
| High | remediate-before-onboarding |
| Medium | proceed-with-conditions |
| Low | proceed-with-conditions |

## Deterministic computations

1. **Domain coverage.** For each required domain, at least one accepted evidence type must be
   present. Any uncovered domain → `insufficient-evidence` (not packaged).
2. **Evidence freshness.** For domains with a freshness window, the freshest item must be
   within `max_age_days` of `as_of_date`. An out-of-window required domain → `stale-evidence`.
3. **Findings fidelity.** Every finding must cite an `evidence_id` present in the bundle, and
   the findings index must be non-empty for a packageable record. An unsupported finding →
   `unsupported-finding`; the package is not assembled.
4. **Residual rating.** Computed per the rubric above; hard gates force `Critical`.
5. **Recommended disposition.** Mapped from the rating; always carries
   `human_adjudication_required: true`.

## Status precedence

`needs-data` (unclassified criticality) → `insufficient-evidence` → `stale-evidence` →
`unsupported-finding` → `draft-assessment`. Only `draft-assessment` is `packageable`.

## What the rules never do

- No onboarding/approval/rejection decision and no risk acceptance.
- No contract signing/execution and no system-of-record update.
- No fabrication — missing or stale evidence is reported, never invented or refreshed on a guess.
