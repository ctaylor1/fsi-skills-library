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
    "reviewed_by":"named accountable reviewer", "method":"exposure-unit-rate-modifier-final-cent",
    "source_refs":["unique-document-version-reference"]
  }}
}
```

Replace the illustrative dates and identity labels with actual case facts. Add the native `data` fields below; do not copy the illustrative values as legal rules. Each `source_refs` is a nonempty array of source_ref values from `sources`. Use unique references for competing versions and retain the conflict as an unresolved issue. Rows may omit unknown facts or use null where documented; they generate explicit evidence gaps. Malformed numeric values, booleans masquerading as numbers and invalid calendar strings fail structural validation. Money and quantities use finite decimal numbers/strings, never formatted currency strings. Zero is known zero; null is unknown. Arrays contain objects; a missing inventory is not automatically empty. All required row IDs are unique within their inventory.

Optional `upstream_artifacts` retain producer envelopes; context changes require the exact reviewed `context_mappings` described by the foundation. Neither an upstream envelope nor profile reviewer label authenticates data or grants authority.

## Workflow fields

- `policy_id`: must match context object; `currency`: ISO-like currency label, never mixed.
- `period`: `{start,end}` inclusive audited policy dates, ending no later than as_of.
- `exposure_ledger_complete`: true only after checking complete audited exposures.
- `rates[]`: `{class_id,class_code,manual_version,basis,unit_size,rate,multiplier,effective_from,effective_to,source_refs}`. Unique class_id; positive unit_size; nonnegative rate and combined multiplier. Rate validity must cover the full policy period. Basis is explicit, e.g. audited-payroll-USD; unit_size 100 means rate per 100 units, not a percentage automatically.
- `exposures[]`: `{exposure_id,basis_record_id,class_id,basis,currency,start,end,exposure,source_refs}`. Unique exposure_id and stable source basis_record_id (the actual payroll/sales row identity, preserved across labels/class changes); exposure is a nonnegative quantity in the rate basis. Class/currency/basis and policy date range must match. Prepare distinct non-overlapping underlying payroll/sales records; two labels for one record cannot create two exposures.
- `control`: `{minimum_premium,fixed_charge,deposit_premium,reported_audit_premium,currency,source_refs}`. All monetary numbers nonnegative or null; zero must be explicit. Control source must document the fixed-charge/minimum calculation order.

Results: traced exposure schedule, manual subtotal, audited premium, deposit adjustment, reported-premium difference and decision boundary. An invalid/unknown calculation basis withholds aggregate money values.

## Output

The immutable draft retains `source_document`, native `results`, detailed `findings`, `unresolved_issues`, case/context/as_of, and the shared artifact. `ready-for-review` means draft readiness. `needs-data` marks source/basis gaps and `needs-review` marks known exceptions. Completeness and evaluability can be downgraded by inherited upstream issues. Human adjudication remains required, approval is `not_requested`, execution is `not_performed`, and `action_taken` is false. Recompute validation detects altered results and retained-source disagreement; content hashes are not signatures.
