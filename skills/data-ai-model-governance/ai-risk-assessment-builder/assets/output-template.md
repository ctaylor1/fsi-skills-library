# AI Risk Assessment — DRAFT (for human review and adjudication)

> Draft AI risk assessment for human review only; this skill does not approve, certify, or
> authorize any AI system for deployment, makes no final risk determination, closes no
> findings, and every residual rating and finding requires review and adjudication by the
> accountable risk owner and approver before any decision.

Fill every `{{placeholder}}` from validated, cited sources. Do not add a risk statement that
is not backed by a listed source. Do not mark any item approved, accepted, or closed — the
approval block stays `pending`.

## 1. System identity

| Field | Value |
| ----- | ----- |
| Assessment ID | {{assessment_id}} |
| System / model | {{system_name}} |
| Use case | {{use_case}} |
| Model reference | {{model_ref}} |
| Intake reference | {{intake_ref}} |
| Inherent risk tier (from intake) | {{inherent_risk_tier}} |
| Framework version | {{framework_version}} |

## 2. Overall result

| Field | Value |
| ----- | ----- |
| Overall residual rating | {{overall_residual_rating}} |
| Findings (High / Medium / Low) | {{findings_high}} / {{findings_medium}} / {{findings_low}} |
| Pack status | {{pack_status}} |

## 3. Domain scoring (all ten required)

Each domain: likelihood x impact → inherent band; control coverage → residual band. Controls
reduce likelihood, never impact; residual is never zero. Every row cites a source.

| Domain | Likelihood | Impact | Inherent | Coverage | Residual | Citations |
| ------ | ---------- | ------ | -------- | -------- | -------- | --------- |
| Data | {{data_L}} | {{data_I}} | {{data_inherent}} | {{data_coverage}} | {{data_residual}} | {{data_citations}} |
| Model | {{model_L}} | {{model_I}} | {{model_inherent}} | {{model_coverage}} | {{model_residual}} | {{model_citations}} |
| Fairness | {{fairness_L}} | {{fairness_I}} | {{fairness_inherent}} | {{fairness_coverage}} | {{fairness_residual}} | {{fairness_citations}} |
| Explainability | {{expl_L}} | {{expl_I}} | {{expl_inherent}} | {{expl_coverage}} | {{expl_residual}} | {{expl_citations}} |
| Security | {{sec_L}} | {{sec_I}} | {{sec_inherent}} | {{sec_coverage}} | {{sec_residual}} | {{sec_citations}} |
| Privacy | {{priv_L}} | {{priv_I}} | {{priv_inherent}} | {{priv_coverage}} | {{priv_residual}} | {{priv_citations}} |
| Third parties | {{tp_L}} | {{tp_I}} | {{tp_inherent}} | {{tp_coverage}} | {{tp_residual}} | {{tp_citations}} |
| Human oversight | {{ho_L}} | {{ho_I}} | {{ho_inherent}} | {{ho_coverage}} | {{ho_residual}} | {{ho_citations}} |
| Resilience | {{res_L}} | {{res_I}} | {{res_inherent}} | {{res_coverage}} | {{res_residual}} | {{res_citations}} |
| Monitoring | {{mon_L}} | {{mon_I}} | {{mon_inherent}} | {{mon_coverage}} | {{mon_residual}} | {{mon_citations}} |

## 4. Findings register (open — for adjudication)

Each finding is `open` and requires adjudication. Do not mark any finding closed, resolved,
or waived.

| Finding | Domain | Severity | Gap controls | Recommended remediation | Owner | Source refs |
| ------- | ------ | -------- | ------------ | ----------------------- | ----- | ----------- |
| {{finding_id}} | {{finding_domain}} | {{finding_severity}} | {{finding_gaps}} | {{finding_remediation}} | {{finding_owner}} | {{finding_sources}} |

## 5. Approval routing (pending — not a decision)

| Field | Value |
| ----- | ----- |
| Approval status | pending |
| Required approvers | {{required_approvers}} |
| Adjudication required | true |

- [ ] All ten domains scored and cited against the current framework.
- [ ] Residual ratings reviewed; overrides (if any) documented with rationale.
- [ ] Every finding has an owner, remediation, and target date.
- [ ] Residual risk decision (mitigate / accept / reject) recorded by the accountable owner.

Reviewer: ________________________  Date: ____________
Approver: ________________________  Decision: adjudicate (approve / accept-with-conditions / reject)
