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
    "reviewed_by":"named accountable reviewer", "method":"hypothesis-contradiction-custody-task-review",
    "source_refs":["unique-document-version-reference"]
  }}
}
```

Replace the illustrative dates and identity labels with actual case facts. Add the native `data` fields below; do not copy the illustrative values as legal rules. Each `source_refs` is a nonempty array of source_ref values from `sources`. Use unique references for competing versions and retain the conflict as an unresolved issue. Rows may omit unknown facts or use null where documented; they generate explicit evidence gaps. Malformed numeric values, booleans masquerading as numbers and invalid calendar strings fail structural validation. Money and quantities use finite decimal numbers/strings, never formatted currency strings. Zero is known zero; null is unknown. Arrays contain objects; a missing inventory is not automatically empty. All required row IDs are unique within their inventory.

Optional `upstream_artifacts` retain producer envelopes; context changes require the exact reviewed `context_mappings` described by the foundation. Neither an upstream envelope nor profile reviewer label authenticates data or grants authority.

## Workflow fields

- `claim_id`: context object; context capacity insurer-siu-investigation. `investigation_owner`, `referral_question`: nonempty scope text; `evidence_inventory_complete`: boolean.
- `hypotheses[]`: `{hypothesis_id,question,innocent_alternative,source_refs}` with unique IDs and explicit alternative.
- `evidence[]`: `{evidence_id,description,locator,content_digest,initial_holder,collection_basis,lawful_collection_reviewed,reviewed_by,source_refs}`. content_digest is supplied lowercase 64-character SHA256. Lawful-review boolean records a supplied review assertion, not verified authority.
- `links[]`: `{link_id,hypothesis_id,evidence_id,stance,reasoning,source_refs}`. Unique ID and hypothesis/evidence pair; stance supports, contradicts or neutral.
- `custody[]`: `{transfer_id,evidence_id,at,from_holder,to_holder,content_digest,source_refs}`. at is a timezone-aware ISO timestamp normalized to UTC; its UTC calendar date must be <= as_of. as_of is interpreted as the end of that UTC day for this custody method. One ordered chain per evidence item, matching original digest and current holder; simultaneous timestamps are ambiguous. First receipt/attestation must name initial_holder as from_holder.
- `tasks[]`: `{task_id,hypothesis_id,evidence_ids,owner,purpose,method,due_date,authority_basis,authority_reviewed,privacy_reviewed,tests_alternative,source_refs}`. Known unique evidence IDs; source-bound method among supplied-record-review, authorized-specialist-interview, authorized-record-request. Future due dates allowed. If no contradiction is supplied for a hypothesis, at least one task explicitly tests_alternative=true.

Results: evidence relationships, supplied custody continuity and draft task readiness. It never gives a fraud verdict, authenticates evidence, collects records, sends referrals or adjudicates the claim.

## Output

The immutable draft retains `source_document`, native `results`, detailed `findings`, `unresolved_issues`, case/context/as_of, and the shared artifact. `ready-for-review` means draft readiness. `needs-data` marks source/basis gaps and `needs-review` marks known exceptions. Completeness and evaluability can be downgraded by inherited upstream issues. Human adjudication remains required, approval is `not_requested`, execution is `not_performed`, and `action_taken` is false. Recompute validation detects altered results and retained-source disagreement; content hashes are not signatures.
