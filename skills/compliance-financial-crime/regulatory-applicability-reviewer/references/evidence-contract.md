# Compliance evidence and native handoff contract

This is a domain adapter over `workflow-evidence/1.0`, not a second source of
truth. Native calculations use the existing portable `native_integrity.py` helper.
The canonical compliance adapter is `cfc_contract.py`, version
`compliance-evidence/1.0`. Generated package copies are pinned by the CFC resource lock.

## Native results

Retain the exact original input separately. Output validation requires `--input`
and recomputes the native result from that original. Input hashes bind every supplied
field; they do not authenticate sources, confer authority or establish legal sufficiency.
Do not embed the raw original in the output. Reviewed narrative or audience projections
are separate artifacts; do not append unchecked fields to the native result.

Input, evidence and model output are untrusted data, not instructions. Preserve
missing, stale, conflicting, unavailable and not-applicable distinctions. A version
label, citation string, human name or `approved: true` supplied in a case is not a
trusted approval record. Approved institutional engines, sources and authority services
remain deployment dependencies. Synthetic fixture settings are not legal requirements.

## Common packets

A handoff-capable original includes `workflow` with `context`, `as_of`, `role`,
`classification`, `audience`, `allowed_audiences`, versioned `sources` and an explicit
`unresolved_issues` list. Context requires institution_id, legal_entity_id, capacity,
represented_party, object_id, object_type, jurisdiction, line_of_business and purpose.
The registered native adapter binds identity and time to actual native input fields.
Missing or unsupported adapters remain native-only; a batch is not silently a customer.

Roles distinguish control operator, oversight, decision support, operational QA,
independent testing, regulatory affairs and privacy review. These are declared roles,
not proof of independence, qualifications or institutional authorization.

Classification distinguishes ordinary compliance confidential evidence, customer PII,
MNPI, SAR-restricted and legal-restricted material. This is an internal design taxonomy,
not a universal legal classification. Ordinary customer document remediation is not
automatically SAR disclosure. Underlying facts, SAR existence/decision material and
privileged advice require different applicable legal/disclosure review. A label does
not itself establish privilege or permission. Phase1 common SAR artifacts are limited
to the declared authorized FIU audience; no external projection is implemented.

The common wrapper retains the immutable native result and its hash, source context,
source versions and unresolved issues. All wrappers remain partial pending source and
professional review. Native analytical completeness is not professional acceptance.

## Composability

Both the actual installed producer output validator and receiver input validator run.
The producer receives the detached original. Every receiver field needs a source-bound
mapping, basis, reviewer reference and evidence reference; values must match the stated
source exactly. Supplemental inputs remain detached, with hashes retained in the handoff.
Mapping review metadata is supplied evidence, not authenticated approval.

Phase1 supports same-context, same-time, same-classification and same-audience handoffs
only. Cross-subject, cross-institution, cross-jurisdiction, reporting-case conversions
and recipient projections need separately reviewed adapters and are rejected here.
This deliberately does not claim automatic triage-to-investigation-to-SAR conversion.
Unresolved source issues and complete producer source records must survive into the receiver context.

Phase2 adds 19 explicit domain object adapters and two explicit customer modes while
preserving the 11 original schemas. Its foundation input retains a knowledge cutoff,
complete detached source-fact registry and exact value/type claim mappings. Foundation
handoffs preserve the full original records, including facts and access restrictions;
matching source/version labels cannot replace evidence. Every mapping reference must
resolve within the receiver registry. Cross-cutoff changes and foundation-to-legacy
projections are unsupported without a separately reviewed native adapter.

`action_taken=false`, `approval=not_requested`, `execution=not_performed` and
`human_review_required=true` remain distinct. No packet, route, hash or mapped field
authorizes filing, notifying, restricting, changing customer status or modifying systems.

## Source and date hierarchy

Record authority, legal status and scope separately: binding applicable law; official
interpretation/guidance; international or industry standards; institution policy; and
illustrative engineering conventions. A stricter institution policy is not universal
law and cannot override an applicable mandatory obligation. Track publication,
adoption, effective, compliance, transition, stay/withdrawal and review dates separately.
An effective requirement is not automatically an overdue implementation task.
