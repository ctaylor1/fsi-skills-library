# Phase 2 native workflow foundation

The native method owns the business analysis. The shared helper validates case,
context, calendar date, versioned source identities and the retained source document;
it preserves unknowns and recomputes output for validation. These checks do not
authenticate evidence or grant authority. A valid incomplete input can produce a
useful gap report. Read status, findings and completeness together with native
results; a local subcheck cannot override unresolved upstream evidence.

Use explicit `unresolved_issues: []` only after reviewing the supplied scope. Optional
`upstream_artifacts` retain original producer artifacts and their unresolved issues.
Map the actual receiver's native `data`; an artifact cannot replace those fields.
Future-dated sources or upstream artifacts cannot support an earlier as-of review.

When upstream capacity, represented party, object, jurisdiction or line differs,
provide exactly one reviewed mapping for that artifact in `context_mappings`:

```json
{
  "source_artifact_hash": "SHA-256 from insurance_contract.stable_hash(source_artifact)",
  "source_context": {"capacity": "...", "represented_party": "...", "object_id": "...", "jurisdiction": "...", "line_of_business": "..."},
  "target_context": {"capacity": "...", "represented_party": "...", "object_id": "...", "jurisdiction": "...", "line_of_business": "..."},
  "reviewed_by": "Named accountable mapper",
  "basis": "Source-backed relationship and scope transition",
  "source_refs": ["a supplied versioned mapping source"]
}
```

Both contexts must match the actual artifact and receiver exactly. Missing,
ambiguous or stale mappings leave the result incomplete. Recording a mapper's name
is an assertion for institutional review, not identity authentication. Mapping
does not remove upstream issues or broaden a package's supported method.

Output retains `source_document`, native `results`, `findings`, `unresolved_issues`,
`completeness` and `evaluability`. `ready-for-review` denotes draft readiness only;
approval remains `not_requested`, execution `not_performed`, and action_taken false.
Output validation runs the native method again; resealing a modified output with a
new hash cannot make different arithmetic or decisions valid.
