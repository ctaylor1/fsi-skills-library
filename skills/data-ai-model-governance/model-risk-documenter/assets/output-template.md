# Model Documentation & Validation-Evidence Pack — DRAFT (for human review and adjudication)

> Draft model documentation pack for human review only; this skill assembles and traces
> evidence but does not validate, approve, attest, or certify any model or AI system, makes no
> fitness-for-use determination, closes no findings, and every section, finding, and approval
> requires review and adjudication by the model owner, independent validation, and the approver
> before any decision.

Fill every `{{placeholder}}` from validated, cited sources. Do not mark a section `documented`
without a versioned source artifact, do not record an approval without a citation, and do not
mark any item validated, approved, attested, or closed — the attestation block stays `pending`.

## 1. Model identity

| Field | Value |
| ----- | ----- |
| Model ID | {{model_id}} |
| Model name | {{model_name}} |
| Model type | {{model_type}} |
| Model version | {{model_version}} |
| Model tier (materiality) | {{model_tier}} |
| Framework version | {{framework_version}} |
| Template version | {{template_version}} |

## 2. Pack result

| Field | Value |
| ----- | ----- |
| Pack status | {{pack_status}} |
| Readiness | {{readiness}} |
| Sections documented / gap / needs-data | {{documented}} / {{gap}} / {{needs_data}} |
| Artifacts cited | {{artifacts_cited}} |
| Findings (High / Medium / Low) | {{findings_high}} / {{findings_medium}} / {{findings_low}} |

## 3. Section traceability (all ten required)

Each section: content + a versioned source artifact → `documented`; content but no traceable
version, or missing required coverage → `gap`; no content → `needs-data`. Every `documented`
row cites at least one versioned artifact.

| Section | Status | Coverage | Source artifacts (citations) | Owner |
| ------- | ------ | -------- | ---------------------------- | ----- |
| Purpose | {{purpose_status}} | {{purpose_coverage}} | {{purpose_citations}} | {{purpose_owner}} |
| Methodology | {{methodology_status}} | {{methodology_coverage}} | {{methodology_citations}} | {{methodology_owner}} |
| Data | {{data_status}} | {{data_coverage}} | {{data_citations}} | {{data_owner}} |
| Performance | {{performance_status}} | {{performance_coverage}} | {{performance_citations}} | {{performance_owner}} |
| Limitations | {{limitations_status}} | {{limitations_coverage}} | {{limitations_citations}} | {{limitations_owner}} |
| Controls | {{controls_status}} | {{controls_coverage}} | {{controls_citations}} | {{controls_owner}} |
| Monitoring | {{monitoring_status}} | {{monitoring_coverage}} | {{monitoring_citations}} | {{monitoring_owner}} |
| Changes | {{changes_status}} | {{changes_coverage}} | {{changes_citations}} | {{changes_owner}} |
| Approvals | {{approvals_status}} | {{approvals_coverage}} | {{approvals_citations}} | {{approvals_owner}} |
| Traceability | {{traceability_status}} | {{traceability_coverage}} | {{traceability_citations}} | {{traceability_owner}} |

## 4. Findings register (open — for adjudication)

Each finding is `open` and requires adjudication. Do not mark any finding closed, resolved, or
waived. Documentation gaps (`DOC-###`) and carried validation findings are both listed.

| Finding | Section | Severity | Reason / gap | Recommended remediation | Owner | Source refs |
| ------- | ------- | -------- | ------------ | ----------------------- | ----- | ----------- |
| {{finding_id}} | {{finding_section}} | {{finding_severity}} | {{finding_reason}} | {{finding_remediation}} | {{finding_owner}} | {{finding_sources}} |

## 5. Approvals on record (evidence only — not a decision)

Record only approvals that carry a cited reference. Uncited approvals are listed under
"unsupported" and are NOT recorded as evidence (no false attestation).

| Approval | Approver role | Decision | Scope | Date | Reference |
| -------- | ------------- | -------- | ----- | ---- | --------- |
| {{approval_id}} | {{approver_role}} | {{approval_decision}} | {{approval_scope}} | {{approval_date}} | {{approval_reference}} |

Unsupported (uncited) approvals flagged: {{unsupported_approvals}}

## 6. Attestation routing (pending — not a decision)

| Field | Value |
| ----- | ----- |
| Attestation status | pending |
| Required approvers | {{required_approvers}} |
| Adjudication required | true |

- [ ] All ten sections assembled and traced to versioned artifacts against the current template.
- [ ] Every `gap`/`needs-data` section has an owner, remediation, and target date.
- [ ] Every carried validation finding reviewed; none closed by this pack.
- [ ] Approvals reconciled to cited memos; no approval recorded without evidence.
- [ ] Documentation-complete / model-validated determination recorded by the accountable owner.

Reviewer: ________________________  Date: ____________
Approver: ________________________  Decision: adjudicate (validated / conditions / not-validated)
