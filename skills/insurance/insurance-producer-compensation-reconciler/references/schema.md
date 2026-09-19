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
    "reviewed_by":"named accountable reviewer", "method":"earned-base-rate-split-linked-chargeback",
    "source_refs":["unique-document-version-reference"]
  }}
}
```

Replace the illustrative dates and identity labels with actual case facts. Add the native `data` fields below; do not copy the illustrative values as legal rules. Each `source_refs` is a nonempty array of source_ref values from `sources`. Use unique references for competing versions and retain the conflict as an unresolved issue. Rows may omit unknown facts or use null where documented; they generate explicit evidence gaps. Malformed numeric values, booleans masquerading as numbers and invalid calendar strings fail structural validation. Money and quantities use finite decimal numbers/strings, never formatted currency strings. Zero is known zero; null is unknown. Arrays contain objects; a missing inventory is not automatically empty. All required row IDs are unique within their inventory.

Optional `upstream_artifacts` retain producer envelopes; context changes require the exact reviewed `context_mappings` described by the foundation. Neither an upstream envelope nor profile reviewer label authenticates data or grants authority.

## Workflow fields

- `agency_id`: context object; `currency`: one ledger currency; `period:{start,end}`: inclusive earned-activity interval ending by as_of; `ledger_complete`: boolean completeness assertion.
- `agreements[]`: `{agreement_id,basis,earning_trigger,rate,effective_from,effective_to,source_refs,splits}`. Rate is decimal fraction in [0,1]. `splits[]` contains `{producer_id,share,source_refs}`, unique producers, nonnegative decimal shares totaling exactly 1.
- `events[]`: `{event_id,agreement_id,policy_id,kind,date,basis,currency,source_refs}`. Unique event IDs. `kind:earned` additionally supplies `base_amount` and `trigger_evidence` equal to the reviewed agreement earning_trigger. `kind:chargeback` additionally supplies `reverses_id` of an earlier in-period earned event , `chargeback_basis` identifying the contract clause/approved entitlement and `fraction` in [0,1]. Cumulative fractions cannot exceed 1. Source_refs establish contractual chargeback basis, not just a cancellation event.
- `reported[]`: `{producer_id,net_earned,currency,source_refs}` for exactly all split recipients. Values are nonnegative period net earnings under this bounded method; negative balances from prior periods need a payable roll-forward method.

Results: event gross/split register, period net earned by producer and differences to reported controls. Unrounded decimals preserve arithmetic; payment rounding and payment execution remain outside this output.

## Output

The immutable draft retains `source_document`, native `results`, detailed `findings`, `unresolved_issues`, case/context/as_of, and the shared artifact. `ready-for-review` means draft readiness. `needs-data` marks source/basis gaps and `needs-review` marks known exceptions. Completeness and evaluability can be downgraded by inherited upstream issues. Human adjudication remains required, approval is `not_requested`, execution is `not_performed`, and `action_taken` is false. Recompute validation detects altered results and retained-source disagreement; content hashes are not signatures.
