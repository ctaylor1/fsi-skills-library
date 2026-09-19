# Native input and output contract

Top level: `case_id`, calendar `as_of`, `context` with capacity, represented_party,
object_id, jurisdiction and line_of_business, versioned `sources`, explicit
`unresolved_issues`, optional `upstream_artifacts`, `rule_profile`, and native `data`.
Each source has source_ref and version, with optional source as_of. Duplicate source
IDs reject; distinguish versions explicitly. All domain evidence rows reference the
source registry through source_refs. Missing business amounts are JSON null; numeric
strings or numbers must be finite. Booleans are not monetary numbers.

Rule profile: profile_id, version, source_refs, effective_from, effective_to,
jurisdictions and lines_of_business. The profile is supplied reviewed evidence, not
a built-in legal opinion. Dates must be YYYY-MM-DD. The complete example documents
native field names and supported enums alongside the method reference.

Output: standardized case/context/as_of, source_document, findings, native results,
status, completeness, evaluability, unresolved_issues and insurance artifact. Status
ready-for-review is a draft readiness state only. Null means unknown/unavailable,
not zero. Review findings may exist in an otherwise evaluable draft. No output
selects a professional outcome or executes an action.

## Native `data` fields

Required evidence sections for a useful matrix are the `policy` object and the
`facts`, `clauses` and `hypotheses` arrays. Omitted arrays become empty lists; an
empty hypothesis list is a data gap. Do not substitute null for an array or object.
Row IDs must be nonblank and unique within their respective array.

| Field | Contract and behavior |
| --- | --- |
| `policy.policy_id` | Nonblank policy identifier. |
| `policy.insured_id` | Nonblank policy insured identifier. |
| `policy.wording_version` | Nonblank version of supplied operative wording. |
| `policy.coverage_trigger` | `occurrence`, `claims_made` or `other`. Missing/unsupported trigger is a gap. `other` requires practitioner interpretation; it does not introduce a new automated trigger method. |
| `policy.effective`, `policy.expiry` | Dates defining the supplied half-open interval `[effective, expiry)`, with effective strictly before expiry. |
| `policy.source_refs` | Registered references for identity, wording and dates. |
| `reported_insured_id` | Nonblank insured identity from the reported claim. A difference from `policy.insured_id` creates a review finding, not a coverage denial. |
| `loss_date` | Date mechanically compared with the supplied policy interval. |
| `claim_made_date`, `reported_date`, `retroactive_date` | Dates required when trigger is `claims_made`; missing values create gaps. The helper preserves these dates but does not determine claims-made trigger satisfaction or reporting-extension applicability. |

Each `facts[]` row has unique `fact_id`, nonblank `quote`, and nonempty registered
`source_refs`. Each `clauses[]` row similarly has unique `clause_id`, nonblank
`quote`, and `source_refs`. Quotes remain supplied evidence; the helper does not
verify authenticity or label allegations as proven facts.

Each `hypotheses[]` row contains:

| Field | Contract |
| --- | --- |
| `hypothesis_id` | Required unique nonblank string. |
| `effect` | Exactly `potential_grant`, `potential_exclusion`, `potential_exception`, `condition` or `unknown`. Missing/other values reject. |
| `clause_ids` | Array of known clause IDs; at least one for an adequately supported hypothesis. |
| `supporting_fact_ids` | Array of known fact IDs; at least one for an adequately supported hypothesis. |
| `contrary_fact_ids` | Array of known fact IDs; explicit empty array documents no identified contrary facts after review. Omission becomes empty but does not satisfy the separate review attestation. |
| `contrary_evidence_reviewed` | JSON `true` for a completed contrary-evidence review. Other/missing values create a gap. |
| `source_refs` | Registered evidence for the interpretation and mapping. |

Missing clause/support lists create data gaps. References to nonexistent fact or
clause IDs reject the input; duplicate/missing row IDs also reject. Null or malformed
list shapes are not supported. Missing/null dates and text remain gaps; malformed
non-null dates reject. Blank text or literal `unknown`, `n/a` or `na` does not satisfy
identity, quotation or wording fields. Source gaps and future-dated cited evidence
remain visible. Contrary facts, an insured mismatch and an out-of-period loss create
review findings. Every claims-made review still carries a specialist-review finding,
even when all dates are supplied.

## Native results

`loss_within_supplied_period` is true/false when the three required interval/loss
dates are usable, otherwise null. It is not a coverage conclusion. `facts` and
`clauses` preserve the source rows. `coverage_hypotheses` preserves each hypothesis
and adds `assessment: hypothesis_for_review` and `source_linked` (a reference-linkage
boolean). `coverage_determination` is always `not_made`; `reservation_of_rights` is
always `not_issued`. The authorized claims coverage specialist remains decision owner.
