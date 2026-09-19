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
    "reviewed_by":"named accountable reviewer", "method":"supplied-rights-net-pro-rata-interest",
    "source_refs":["unique-document-version-reference"]
  }}
}
```

Replace the illustrative dates and identity labels with actual case facts. Add the native `data` fields below; do not copy the illustrative values as legal rules. Each `source_refs` is a nonempty array of source_ref values from `sources`. Use unique references for competing versions and retain the conflict as an unresolved issue. Rows may omit unknown facts or use null where documented; they generate explicit evidence gaps. Malformed numeric values, booleans masquerading as numbers and invalid calendar strings fail structural validation. Money and quantities use finite decimal numbers/strings, never formatted currency strings. Zero is known zero; null is unknown. Arrays contain objects; a missing inventory is not automatically empty. All required row IDs are unique within their inventory.

Optional `upstream_artifacts` retain producer envelopes; context changes require the exact reviewed `context_mappings` described by the foundation. Neither an upstream envelope nor profile reviewer label authenticates data or grants authority.

## Workflow fields

- `claim_id`: context object; `currency`: one currency; `rights_inventory_complete` and `collection_ledger_complete`: explicit booleans. An explicitly empty `collections` list means no recorded collections; omission is a gap.
- `rights[]`: `{right_id,right_type,debtor_id,rights_basis,reviewed_by,recoverable_limit,limitation_date,source_refs}`. Types: subrogation, salvage, contribution. Limit nonnegative money; date source-reviewed, may be future. Right IDs unique.
- `interests[]`: `{interest_id,right_id,party_id,capacity,interest_amount,currency,source_refs}`. capacity is insurer, claimant or other; unique (right_id,party_id) and interest_id; nonnegative money with strictly positive total for each right.
- `collections[]`: `{collection_id,right_id,date,gross_amount,cost_amount,cost_deduction_reviewed,currency,source_refs}`. Unique IDs; dates no later than as_of; gross and cost nonnegative with cost <= gross. Cost basis must be reviewed even when cost is zero.
- `tasks[]`: `{task_id,right_id,task,owner,due_date,source_refs}`. Unique IDs; future due dates allowed. The source-bound due date is not calculated from an assumed legal deadline.

Results: rights/limitation register, gross/cost/net collection register, unrounded pro-rata allocation, draft preservation tasks. No legal rights verdict, demand or disbursement is implied.

## Output

The immutable draft retains `source_document`, native `results`, detailed `findings`, `unresolved_issues`, case/context/as_of, and the shared artifact. `ready-for-review` means draft readiness. `needs-data` marks source/basis gaps and `needs-review` marks known exceptions. Completeness and evaluability can be downgraded by inherited upstream issues. Human adjudication remains required, approval is `not_requested`, execution is `not_performed`, and `action_taken` is false. Recompute validation detects altered results and retained-source disagreement; content hashes are not signatures.
