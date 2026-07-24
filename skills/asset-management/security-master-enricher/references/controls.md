# Controls — security-master-enricher

- **Risk tier:** R2 — analytical / drafting. **Action mode:** Draft-only; no system-of-record
  change.
- **Human approval:** `external-delivery` — required before the enrichment pack or any proposal
  is delivered externally or written to the security master. Internal analytical use may be
  reviewer-sampled.

## Prohibited (fail closed)

- **No creation / no write.** The skill never creates a production security, writes to the
  security master, or promotes a record to golden/production. Every proposal is
  `status: "PROPOSED"`.
- **No identity resolution.** The skill never chooses between conflicting identifiers and never
  merges records. `identifier_conflict` and `identifier_invalid` are queued for a steward with
  **no** proposed value.
- **No source adjudication.** Selecting the top-ranked value on an `attribute_conflict` is a
  draft pending steward review, not a decision that a source is correct.
- **No silent correction / no suppression.** Data-quality issues (stale, missing, unpermitted)
  are surfaced in the conflict queue, never quietly fixed or dropped.
- **No per-job threshold tuning.** Required/material fields, tolerance, freshness window, and
  source ranking come only from the versioned `config`.
- **No investment advice.** The skill enriches reference/static data; it never recommends
  buying, selling, or weighting any security or issuer (MNPI / client-confidential data).

## Required output screens (`scripts/validate_output.py`)

- **Tie-out:** field dispositions account for every field (`agreed + conflicted + missing +
  absent == securities × 8`, `residual == 0`); attribute proposals `== agreed + conflicted`;
  `len(conflict_queue) == Σ counts by type`; `summary.by_conflict_type` matches the queue.
- **Conflict taxonomy:** every conflict's `type` is in the fixed set with an id, field,
  severity, and candidate list.
- **Provenance:** every proposal cites ≥1 approved source.
- **Identity boundary:** identity conflicts carry no `proposed_value`, require steward review,
  and have no matching identifier proposal.
- **Proposed-only / prohibited-decision:** every proposal `status == "PROPOSED"`; no
  applied/created/merged status; no creation/resolution-completed language; no investment-advice
  language.
- **Idempotency:** `enrichment_id` derived from `entity/as_of + input_fingerprint`
  (64-hex content hash), no timestamp/random component.
- **Disclaimer:** the standing no-creation/no-resolution disclaimer is present.

## Segregation of duties

- The skill **joins, proposes, and queues**. A different, authorized **security-master
  steward** (data governance) reviews, approves, and posts (creates the security / resolves the
  identity / writes the master). Preparation and posting must not be the same actor.
- The enrichment preparer is not the conflict approver.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Reference-data enrichment needs no
  customer NPI; minimize any position/holdings detail — this skill operates on instrument
  static data, not client positions.
- Retain the enrichment pack, proposals, provenance, conflict queue, and `config_version` per
  records policy; log the read and any external-delivery approval.

## Reproducibility

`enrichment_id` + `input_fingerprint` bind the output to the exact inputs and config version;
re-running the same inputs reproduces the same proposals, conflicts, and tie-out.
