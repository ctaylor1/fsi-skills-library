# Independent Model Validation — Findings DRAFT (for human review and adjudication)

> Draft independent model-validation findings for human review only; this skill does not
> approve, certify, or authorize any model for use, makes no final validation decision, closes
> no findings, assembles no governed model documentation pack, and every finding and recommended
> disposition requires review and adjudication by the model validation lead and approver before
> any decision.

Fill every `{{placeholder}}` from validated, cited sources. Do not add a validation statement
that is not backed by a listed source. Do not credit a `pass` without independent evidence. Do
not mark any item approved, accepted, cleared, or closed — the validation outcome stays
`pending`. The governed model documentation pack (validation report of record) is assembled
separately by `model-risk-documenter`; this draft is validation findings only.

## 1. Model identity

| Field | Value |
| ----- | ----- |
| Validation ID | {{validation_id}} |
| Model ID / name | {{model_id}} — {{model_name}} |
| Model tier (from inventory) | {{model_tier}} |
| Validation type | {{validation_type}} |
| Framework version | {{framework_version}} |

## 2. Overall result

| Field | Value |
| ----- | ----- |
| Overall finding severity | {{overall_finding_severity}} |
| Recommended disposition (recommendation only) | {{recommended_disposition}} |
| Findings (High / Medium / Low) | {{findings_high}} / {{findings_medium}} / {{findings_low}} |
| Areas (passed / deficient / not tested) | {{areas_passed}} / {{areas_deficient}} / {{areas_not_tested}} |
| Pack status | {{report_status}} |

## 3. Validation area assessment (all seven required)

Effective status is independent: a `pass` counts only with the validator's own evidence; a failed
test forces `deficiency`; a developer-attested-only or untested area is `not_tested`. Every row
cites a source.

| Area | Materiality | Declared | Validated (independent) | Independent evidence | Citations |
| ---- | ----------- | -------- | ----------------------- | -------------------- | --------- |
| Conceptual soundness | {{cs_mat}} | {{cs_declared}} | {{cs_validated}} | {{cs_indep}} | {{cs_citations}} |
| Data | {{data_mat}} | {{data_declared}} | {{data_validated}} | {{data_indep}} | {{data_citations}} |
| Performance | {{perf_mat}} | {{perf_declared}} | {{perf_validated}} | {{perf_indep}} | {{perf_citations}} |
| Outcomes analysis | {{out_mat}} | {{out_declared}} | {{out_validated}} | {{out_indep}} | {{out_citations}} |
| Limitations | {{lim_mat}} | {{lim_declared}} | {{lim_validated}} | {{lim_indep}} | {{lim_citations}} |
| Controls | {{ctrl_mat}} | {{ctrl_declared}} | {{ctrl_validated}} | {{ctrl_indep}} | {{ctrl_citations}} |
| Ongoing monitoring | {{mon_mat}} | {{mon_declared}} | {{mon_validated}} | {{mon_indep}} | {{mon_citations}} |

## 4. Findings register (open — for adjudication)

Each finding is `open` and requires adjudication. Do not mark any finding closed, resolved, or
waived.

| Finding | Area | Type | Severity | Recommended remediation | Owner | Source refs |
| ------- | ---- | ---- | -------- | ----------------------- | ----- | ----------- |
| {{finding_id}} | {{finding_area}} | {{finding_type}} | {{finding_severity}} | {{finding_remediation}} | {{finding_owner}} | {{finding_sources}} |

## 5. Validation outcome routing (pending — not a decision)

| Field | Value |
| ----- | ----- |
| Validation outcome status | pending |
| Required approvers | {{required_approvers}} |
| Adjudication required | true |

- [ ] All seven areas assessed and cited against the current framework.
- [ ] Independence confirmed: every credited `pass` rests on the validator's own evidence.
- [ ] Every finding has an owner, remediation, and target date.
- [ ] Validation disposition (approve / approve-with-conditions / reject / restrict use) recorded
      by the accountable approver — not by this skill.
- [ ] Documentation of record assembled by `model-risk-documenter` after adjudication.

Validator: ________________________  Date: ____________
Approver: ________________________  Decision: adjudicate (approve / approve-with-conditions / reject / restrict)
