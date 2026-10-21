# Case quality method

## Scope and identities

The native object is `financial_crime_case_quality_review`; it is the review or batch, not the
underlying investigation case. Each `native_case_id` must equal its exact source-bound `case_id`.
Institution/entity/jurisdiction match workflow context. Retain upstream native artifact ID and
version without claiming that an ID authenticates the producer. The mandate binds the legal
profile ID/version, authority purpose, reviewer, dates, population and selected case IDs.
Duplicate case IDs, record IDs, reference inventories or case/criterion observations, reversed
periods, malformed claims and changed native context fail intake. Null substantive values are
valid partial inputs and withhold their dependents. Preserve all inherited unresolved issues.

## Criteria and observations

Every consequential value is a claim `{value, source_refs, fact_ids}` mapping exactly to supplied
source facts. Criterion kind, procedure, requirement, version, applicability and legal profile
are explicit. No source list, title or claim of access proves the observation occurred.

- `evidence-completeness`: reconcile the case's required exhibit IDs; each exhibit has a case,
  version, availability, capture date and exact source/fact locator. Missing exhibits are quality
  exceptions; unestablished inventories withhold the assessment.
- `chronology-consistency`: verify case-scoped events, evidence exhibits, dates within the case
  period, dates visible at receipt/cutoff, predecessor dates and cycles. Retain contradictions
  as exceptions instead of silently reordering events.
- `reasoning-traceability`: the exact disposition reasoning must be in the observation. Compare
  the supplied material concern, counterevidence and contradiction inventories with the reviewed
  IDs, require case-specific exhibits, rationale, named human review and supplied judgment.
  Exact inventory equality prevents omission and invented rebuttals. It does not prove the
  explanation responds adequately; the qualified human owns that assessment.
- `disposition-traceability`: apply the same reasoning checks, then compare proposed disposition
  values and chronology. A quality pass never confirms the disposition, closes the case or
  decides reportability. The strings remain proposed, source-bound and unverified.
- `tool-source-faithfulness`: use only when explicitly applicable. Require tool/model/prompt/output
  versions, purpose, generation date and human review. Compare each proposed factual value to the
  exact locator in the supplied registry. Do not infer semantic truth, vendor quality, model
  validity, guilt, customer reputation, privilege or decision authority.

An observation's version, test date, reviewer, completed human review, specific rationale and
exhibits must be consistent. A supplied pass cannot override a mechanical exception. Unknown
support makes the eligible result unknown; independently known exceptions remain in the row.
A source-bound human fail with complete supporting workpaper evidence remains fail even when
mechanical link checks find no conflict. This is qualitative human assessment, not automated
substantive reasoning certification.

## Population and proportions

No untested selected case is pass. Counts are by distinct case/criterion. Complete observed case
proportions use unique cases with all applicable criteria observed, with case exceptions counted
once. Partial cases retain known exceptions but are excluded from this denominator; display their
IDs. Proportions are withheld if sample/population/criteria scope, period, profile or sampling
rationale is inconsistent. Always disclose coverage, exact ratio and no population inference.
Threshold comparison additionally requires a supported operational QA/second-line mandate, all
selected cases complete and an exact source-bound decimal string in [0,1]. It uses integer counts
against the exact decimal threshold, not a rounded display or binary float. Fractional JSON
numbers are invalid threshold intake. A threshold result is a supplied criterion comparison,
not acceptance of a program, assurance opinion or decision.

## Independence and professional responsibility

The method records supplied owner assessment, non-involvement, reporting-line, conflict and
competence evidence. Identity/independence is never inferred from `workflow.role`, job title or
an external reviewer label. Statutory independent testing, internal audit and model validation
remain unsupported owner methods even with apparently consistent independence evidence. Their
formal opinions and population inference require their separate mandate and methodology.
