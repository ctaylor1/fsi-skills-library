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
    "reviewed_by":"named accountable reviewer", "method":"continuous-calendar-daily-indemnity-offset",
    "source_refs":["unique-document-version-reference"]
  }}
}
```

Replace the illustrative dates and identity labels with actual case facts. Add the native `data` fields below; do not copy the illustrative values as legal rules. Each `source_refs` is a nonempty array of source_ref values from `sources`. Use unique references for competing versions and retain the conflict as an unresolved issue. Rows may omit unknown facts or use null where documented; they generate explicit evidence gaps. Malformed numeric values, booleans masquerading as numbers and invalid calendar strings fail structural validation. Money and quantities use finite decimal numbers/strings, never formatted currency strings. Zero is known zero; null is unknown. Arrays contain objects; a missing inventory is not automatically empty. All required row IDs are unique within their inventory.

Optional `upstream_artifacts` retain producer envelopes; context changes require the exact reviewed `context_mappings` described by the foundation. Neither an upstream envelope nor profile reviewer label authenticates data or grants authority.

## Workflow fields

- `claim_id`: context object; `benefit_type`: disability or long-term-care; `currency`: one currency; context capacity: carrier-benefits-review or benefits-administrator-review.
- `criteria[]`: `{criterion_id,description,assessor_role,source_refs}`. Unique ID; role medical, vocational or administrative. Description preserves the relevant policy test, including applicable period definition.
- `periods[]`: `{period_id,start,end,source_refs}`. Inclusive distinct benefit intervals, no overlap, no future dates, no start before onset; one interval <= 3661 days.
- `observations[]`: `{observation_id,period_id,criterion_id,start,end,disposition,assessor_role,assessed_by,source_refs}`. Disposition met/unmet/unknown; named assessor in required role. Evidence dates must cover the whole period. Retain conflicting observations as separate IDs.
- `benefit`: `{onset_date,waiting_days,daily_amount,daily_limit,remaining_limit,currency,source_refs}`. waiting_days is a whole nonnegative calendar-day count. Amounts nonnegative or null. The remaining cap is the separately evidenced unused benefit balance as of the reviewed periods, not a new limit inferred by this script.
- `offset_inventory_complete`: boolean; `offsets[]`: `{offset_id,period_id,amount,basis,currency,source_refs}`. Unique offset IDs, explicit policy offset basis, nonnegative period money. Empty complete array means zero; missing/incomplete list is a gap.

Results: criterion/evidence states by period, waiting-period start, gross/offset/net scenarios and aggregate remaining-limit cap. Medical and final benefit decisions are never performed. Each criterion also reports `evidence_basis_valid`: a supplied met label with false evidence validity cannot support gross benefit. Unsupported/invalid method, scope or benefit-source evidence withholds the dependent waiting date and local arithmetic. Invalid period evidence or overlapping periods withhold affected duration and money; invalid observation evidence withholds gross/net for its period. Incomplete or duplicate offset inventory leaves offsets and net unknown (including an empty but incomplete array), preserving valid gross amounts. An unallocated offset prevents treating any period as having zero offsets.

## Output

The immutable draft retains `source_document`, native `results`, detailed `findings`, `unresolved_issues`, case/context/as_of, and the shared artifact. `ready-for-review` means draft readiness. `needs-data` marks source/basis gaps and `needs-review` marks known exceptions. Completeness and evaluability can be downgraded by inherited upstream issues. Human adjudication remains required, approval is `not_requested`, execution is `not_performed`, and `action_taken` is false. Recompute validation detects altered results and retained-source disagreement; content hashes are not signatures.
