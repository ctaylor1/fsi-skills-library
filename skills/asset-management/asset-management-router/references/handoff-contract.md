# Investment handoff contract 1.0

This is an AM adapter over workflow-evidence/1.0, with generated local helpers. Inputs
are detached from result artifacts. Cross-skill packets are **internal-review only**;
external reports require a separate audience-approved projection. No authorization or
source authentication is performed. The preserved native result must already pass its
actual validator with the original input (`--input`).

## Request

`request_id`, `as_of` and `knowledge_cutoff` are required. `context` supplies capacity,
represented_party, object_id, subject_type, line_of_business, jurisdictions, audience,
currency, units and book_basis. Use explicit `not-applicable` for nonnumeric fields;
do not fill genuinely unknown subject facts with placeholders.

`sources` contains unique source_ref, version, economic as_of, known_at and permitted_use.
The last is a supplied use assertion, not a license grant. Known-at dates cannot exceed
the knowledge cutoff; a forecast's economic date can be future if it was already known.
`native_input` is the exact producer/receiver input. `native_identity_pointer` and
`native_as_of_pointer` must equal the authoritative paths in the bundled
`investment_contract.py` native-adapter registry; arbitrary caller-selected fields
cannot establish identity. The actual producer is supplied to artifact assembly.
Standalone requests and all receiver requests require `native_skill` matching the
actual package. The six native-only registry entries cannot yet use common envelopes.
`unresolved_issues` and `upstream_artifacts` preserve incomplete inputs and prior findings.

## Native output and method

Artifact assembly invokes the producer's real source-bound output validator. The
packet retains its native result, original-input digest, method id/version/
implementation_version/origin, knowledge cutoff and a content-bound workflow artifact.
Original documents/snapshots remain in approved detached storage. A full input hash is
not proof of source truth, completeness, legal entitlement or business approval.

## Handoff mapping

The caller supplies a real receiver-native request, a mapping bound to the source
artifact hash and complete proposed target-request hash, reviewed_by and basis. Each
receiver-native leaf is covered either by an exact source JSON-pointer copy or an
additional input with its own source_ref and value_hash. Conversions/calculations require
a separately validated method; this adapter does not infer them. Context changes need
an explicit source/target context_mapping and basis. Reviewer text is not authentication.

The generated handoff retains the source artifact and all its issues. Validation
requires the detached original producer request and reruns the actual producer output
validator, then checks the source packet, reviewed mapping, receiver content hash, issue inheritance,
scope and actual receiver input validator. Envelope validity alone never establishes
native compatibility. Missing mappings/fields, future evidence, altered outputs and
execution/delivery claims fail. An input accepted by a native validator still carries
upstream incompleteness for the receiving practitioner to address.

Standalone library envelope inspection requires explicit `integrity_only=True`; it
is never sufficient for handoff acceptance. Even a rehashed packet must reconstruct
from the detached original using the actual producer validator. CLI handoff commands
require `--source-package` and `--source-request` as well as `--target-package`.

Current native adapters allow only `local-analysis`; external and system-of-record
origins require a separate engine adapter. `method_metadata_assurance` remains
`caller-declared-unverified`; method labels are not institutional acceptance.
