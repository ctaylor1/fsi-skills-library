# Native input and output

Use `schema_version: ir-phase3/1.0` and the common dated, issuer/security-specific
research context in [evidence-standard.md](evidence-standard.md). Required outer
financial basis: `currency`, `units`, `accounting_basis`, `consolidation_scope`.
These, the subject, audience, purpose and barrier must match the retained model.
An outer `issuer_type`, if present, must match `nonfinancial-corporate`.

- `model_kind`: `three-statement-model-builder` or `dcf-modeler`; the actual native
  Phase 2 input schema is retained in `original_model`. No workbook binary is read.
- `model_id`, `base_version`, `proposed_version`: supplied model identity and
  artifact versions. Proposed version must differ; these labels are not registry
  authentication. `config_version` in a native model is distinct configuration.
- `original_model_hash`: canonical SHA-256 of the complete retained original.
- `observed_current: {version, input_hash}` must equal the supplied base version
  and original hash. Capture it independently from the institution's model store;
  this offline method cannot prove the store is still current or lock it.
- `context_transition: {mode, from, to, rationale, evidence_refs}`: `from` and `to`
  contain exactly `as_of`, `knowledge_cutoff`, `use_on`. Mode `same-snapshot`
  requires no date change. `advance-snapshot` requires at least one advance, no
  regression and unchanged date/timestamp precision. All current dates equal the
  outer context. Event framing is immutable. Source availability is checked at
  the current cutoff, never retrospectively assigned to the old snapshot.
- `required_update_paths`: unique, nonempty declared update inventory, exactly
  matching patch paths. Coverage is limited to this supplied inventory.
- `patches`: nonempty, at most 2,000 records, each `{patch_id, path, before_hash,
  value, rationale, evidence_refs}`. Hash the original scalar value with the same
  canonical hash implementation. Paths are canonical absolute JSON pointers;
  duplicates, overlaps, no-ops, missing/null values, additions and deletions fail.
  Citation references must be nonempty and permission-gated at the top level.

A bounded native top/nested key allowlist rejects unrelated annotations, private
notes, credentials and embedded source prose fields before any candidate copy.
The proposal copies the original, replaces only allowlisted existing scalar
fields and synchronizes current dates, request ID, source register and citations.
For a three-statement model it also synchronizes `model_input.as_of`. Original
source records and citations must remain verbatim; add new source versions with
new IDs. Every carried source must have a gated citation. Old and current
unresolved issues are unioned. Context changes are separately hash-ledgered.

`results` contains `candidate_input`, `candidate_input_hash`, the original hash,
version labels, `patch_ledger`, `generated_context_changes`, transition and
coverage. Every patch ledger shows original/replacement values and hashes.
`native_validation` is `not-performed`: a structured proposal can still be
rejected by the actual target model's domain checks. Ineligible cited evidence
withholds the entire result, including candidate and change ledger.

Output validation requires the separately retained full original update request;
a correct digest or caller-supplied pass flag does not replace reconstruction.
