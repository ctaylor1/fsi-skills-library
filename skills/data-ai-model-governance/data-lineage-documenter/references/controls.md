# Controls — data-lineage-documenter

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The lineage document is a *proposal* for data-governance review.
- **Human approval:** `required` — a data-governance owner (Data Governance Office / Chief Data
  Office) and the accountable data steward must review and approve the lineage, its controls,
  and its retention before it is relied on for regulatory reporting, model documentation, or a
  catalog record. This skill drafts and packages only.

## Prohibited (fail closed)

- **Certifying or attesting** the lineage; asserting the data is accurate, complete, correct,
  or fit for regulatory reporting (e.g. BCBS 239).
- **Approving / signing off** the document, or any accuracy / completeness / compliance
  determination about the data product.
- **Self-approving** the document (`governance_approval` stays `pending`).
- **Inventing** a source, owner, control, or transformation; any traced element must cite an
  authoritative source or be flagged `needs-data` / `undocumented-transform`.
- **Writing** lineage back to the data catalog, model registry, or any system of record;
  resolving a data-quality issue.

## Lineage statuses (this skill may set only these)

Per node: `ready-for-review` | `control-gap` | `orphan-node` | `needs-data`. Per edge:
`ready-for-review` | `undocumented-transform` | `dangling-edge`. Package: `draft-incomplete` |
`ready-for-governance-review`. It may **not** set `certified`, `attested`, `approved`,
`accurate`, or any result state.

## Required output screens (`scripts/validate_output.py`)

- Template fidelity: required sections + per-node / per-edge fields present; every node layer is
  in the approved taxonomy (`source, ingestion, transformation, store, feature, output`).
- No unsupported/unapproved claims: a node/edge asserting `traced` provenance cites its source;
  a `ready-for-review` node is fully documented (owner + traced provenance + the attributes its
  criticality requires) and connected; a `ready-for-review` edge documents a transformation
  traced to a source.
- Graph & coverage integrity: `coverage.complete` consistent with node/edge statuses and graph
  soundness; a `ready-for-governance-review` package is genuinely complete, sound, and fully
  ready.
- Required approvals: `governance_approval == "pending"`; `reviewer_signoff_required == true`.
- No certification/attestation/accuracy-determination or catalog/system-of-record-write language
  (regex: "lineage certified", "certified complete/accurate", "we attest", "data is accurate/
  fit for", "fit for regulatory reporting", "BCBS 239 compliant", "sign-off complete", "no
  further review required", "catalog has been updated", "system of record updated").
- Standing note present.

## Segregation of duties

Documenting the lineage, **approving** it, and **operating** the pipeline are distinct control
activities with distinct entitlements. The same person or skill must not both author the lineage
and attest to its accuracy; the data-governance owner / steward approval is independent of the
pipeline engineer who drafts it.

## Data classification, privacy, records

- **Confidential.** Lineage metadata can reveal sensitive data locations and flows; reference
  datasets and systems by catalog id and node id rather than embedding records (data
  minimization). Classification is documented per node, not assumed.
- Retain the drafted lineage document, `spec_version`, source citations, and reviewer/steward
  sign-off with the data-product record per data-governance recordkeeping; log every read and
  every document produced with the author identity.
