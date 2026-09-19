# Native input and output contract

Construct input directly from authorized evidence. This schema is sufficient without the synthetic examples.

```json
{
  "case_id": "durable-case-identifier",
  "as_of": "2026-09-18",
  "context": {
    "capacity": "actual professional or represented capacity",
    "represented_party": "party identifier",
    "object_id": "workflow policy, agency or claim identifier",
    "jurisdiction": "reviewed jurisdiction identifier",
    "line_of_business": "reviewed product identifier"
  },
  "sources": [{"source_ref":"unique-document-version-reference","version":"immutable-version-label","as_of":"2026-09-18"}],
  "unresolved_issues": [],
  "data": {"profile": {
    "profile_id":"reviewed-method-profile", "version":"profile-version",
    "jurisdictions":["reviewed jurisdiction identifier"],
    "lines_of_business":["reviewed product identifier"],
    "effective_from":"2026-01-01", "effective_to":"2026-12-31",
    "reviewed_by":"named accountable reviewer", "method":"claimant-reason-evidence-request-matrix",
    "source_refs":["unique-document-version-reference"]
  }}
}
```

Replace the illustrative dates and identity labels with actual case facts. Add the native `data` fields below; do not copy the illustrative values as legal rules. Each `source_refs` is a nonempty array of source_ref values from `sources`. Use unique references for competing versions and retain the conflict as an unresolved issue. Rows may omit unknown facts or use null where documented; they generate explicit evidence gaps. Malformed numeric values, booleans masquerading as numbers and invalid calendar strings fail structural validation. Money and quantities use finite decimal numbers/strings, never formatted currency strings. Zero is known zero; null is unknown. Arrays contain objects; a missing inventory is not automatically empty. All required row IDs are unique within their inventory.

Optional `upstream_artifacts` retain producer envelopes; context changes require the exact reviewed `context_mappings` described by the foundation. Neither an upstream envelope nor profile reviewer label authenticates data or grants authority.

## Workflow fields

- `claim_id`: context object; `claimant_id`: context represented_party. Context capacity claimant or claimant-representative. `reasons_complete` and `chronology_complete`: explicit booleans for supplied dispute scope.
- `notice`: `{notice_id,received_date,response_due_date,recipient,route,deadline_basis,reviewed_by,source_refs}`. Due date is supplied and source-reviewed, not defaulted. Deadline basis describes governing notice/contract/profile and calendar assumptions.
- `events[]`: `{event_id,date,actor,description,source_refs}`. Unique IDs and no future dates; source-backed factual chronology.
- `reasons[]`: `{reason_id,notice_id,reason_text,provision,source_refs}`. One unique ID per actual adverse reason; notice_id matches notice; provision may explicitly say absent-in-notice when accurate.
- `evidence[]`: `{evidence_id,date,description,locator,source_refs}`. Unique IDs; usable page/record locator, no future source dates.
- `links[]`: `{link_id,reason_id,evidence_id,stance,explanation,source_refs}`. Unique ID and unique reason/evidence pair. Stance supporting, contrary or contextual describes relevance to claimant's position.
- `requests[]`: `{request_id,reason_ids,kind,request_text,source_refs}`. Nonempty unique known reason IDs; kind reconsideration, information or correction. Text states the claimant's concrete request.

Results: ordered chronology, every adverse reason's supporting/contrary/contextual evidence and requests, draft destination/route and supplied response date; no submission or merits determination.

## Output

The immutable draft retains `source_document`, native `results`, detailed `findings`, `unresolved_issues`, case/context/as_of, and the shared artifact. `ready-for-review` means draft readiness. `needs-data` marks source/basis gaps and `needs-review` marks known exceptions. Completeness and evaluability can be downgraded by inherited upstream issues. Human adjudication remains required, approval is `not_requested`, execution is `not_performed`, and `action_taken` is false. Recompute validation detects altered results and retained-source disagreement; content hashes are not signatures.
