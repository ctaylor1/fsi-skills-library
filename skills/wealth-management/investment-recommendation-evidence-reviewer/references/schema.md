# JSON contract — recommendation evidence v0.2

Use `evals/files/request_example.json` as a complete de-identified example. Old v0.1 packets
are not silently accepted: migrate by recovering the underlying sources and explicit policy.
Earlier draft packets without `unresolved_issues` also require source review and explicit issue
mapping before migration; do not automatically fill empty lists merely to pass validation.

## Common envelope
`schema_version: wealth-p0-v1`; nonempty `request_id`, `household_id`; `as_of: YYYY-MM-DD`;
`engagement: {capacity: advisory|brokerage|private-bank|trust, jurisdiction: US}`;
`sources: [{source_id, reference, owner, as_of, valid_until}]`. Registry identities are unique;
each source must satisfy source.as_of <= request.as_of <= valid_until. Numbers must be finite.
The bundled `scripts/wealth_contract.py` is synchronized from the repository canonical helper.

## Domain fields
- `recommendation`: `recommendation_id`, `action` (buy/sell/hold/switch/exchange/rollover/reallocate/
  account_open/account_transfer), `date`, `source_ids`. Account-level recommendations do not
  require a fictitious security.
- `applicability`: `profile_id`, `version`, `owner`, `reviewed_by`, `reviewed_on`, `rationale`,
  `capacity`, `jurisdiction`, `context: general|retirement`, `basis` (see domain rules),
  `disclosure_deadline`, `source_ids`. Missing profile facts cause needs-data; a wrong capacity
  or jurisdiction cannot silently select a different legal basis. Policy records are supplied
  evidence and are not authenticated by the scripts.
- `evidence`: a list, possibly empty, with at most one record for each documented check ID.
  Record: `check_id`, `assessment: documented|incomplete`, `reviewed_by`, `recorded_on`,
  `source_ids`, `items` list, and required `unresolved_issues` list. Unknown or duplicate check IDs
  and malformed structures reject. `unresolved_issues: []` is an explicit reviewer representation
  after substantive review, not a default to insert for unreviewed material.
- Each unresolved issue: nonempty `code`, `message`, `source_ids` list and
  `origin: source-review|upstream-artifact`. Upstream origin requires
  `upstream_artifact: {skill, artifact_id, input_hash}` with nonempty identifiers and SHA-256 hex
  digest; retain the original upstream issue code/message and cite its source facts. Missing or
  unknown issue source IDs keep the review incomplete. The reference is supplied provenance,
  not proof that the upstream artifact was retrieved or authenticated. See the handoff mapping.
- Each item: unique-within-record `item_id`, permitted `kind`, nonempty `description`,
  `subject_id` equal to recommendation_id, nonempty `source_ids` resolving in the registry.
  Disclosure items additionally require `disclosure_id`, `version`, `delivered_on`.
  All material evidence, including policy and recommendation, needs item-level source IDs.

The required kind set is maintained in `references/domain-rules.md` and enforced by
`scripts/domain.py`. An empty item list remains incomplete even if assessment says documented.
Unknown sources are unresolved data, never converted to placeholder citations.

## Output and validation
The common envelope is read-only, human-review-required and not-delivered. `result` contains
`input_snapshot` (these structured inputs only), `checks` (all 11 IDs), `counts`,
`applicability_status`, `determination: not-made`, and `scope`. Each check preserves item evidence
and issues, including the complete structured `unresolved_issues` with provenance. Missing,
incomplete, policy or substantive unresolved issues force `status: needs-data`; otherwise review-ready.
Nonempty unresolved issues override a documented assessment and conditional inapplicability.

`validate_output.py` rebuilds from input_snapshot and compares the entire output, including
hash, sources, context, findings and the exact inventory. Extra approval/decision fields,
omitted checks and changed metrics fail. The hash binds content; it is not an authorization token.
The validator detects dropped issues in an output relative to its input snapshot. It cannot detect
an issue omitted before input construction, or a consistently rewritten snapshot and output, without
the original externally held source artifact and input hash. Source review remains required.

### Unknown review attribution

Use null for an evidence record's missing `reviewed_by` or `recorded_on`; the
calculator records incomplete evidence. A profile reviewer, source owner, document
receipt date or routing owner cannot supply these facts by inference. Keep proposed
follow-up assignments separate from completed human reviews.
