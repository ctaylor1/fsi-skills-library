# Domain Rules — security-master-enricher

Deterministic security-master enrichment: how candidate identifier and attribute observations
are **joined** across ranked approved sources, how one value per field is **proposed**, how
disagreements and data-quality issues are **classified** into a fixed **conflict taxonomy**,
how the result **ties out**, and how identities are handled (**never resolved** by this skill).
Required fields, material fields, tolerances, the freshness window, and the source ranking are
configuration (versioned, owned by Asset Management investment & product), not hard-coded
judgments.

## Enrichment field registry

Every candidate security is evaluated against exactly these enrichment fields:

```
currency | exchange | asset_class | maturity | coupon | rating | benchmark | issuer
```

`coupon` is numeric (compared within `numeric_tolerance`); the others are string-normalized
(trimmed, case-folded) for the agreement test. Identifiers (`ISIN`, `CUSIP`, `SEDOL`,
`TICKER`, …) are handled separately from attributes because identity is a hard boundary.

## Source hierarchy & selection (deterministic)

`source_hierarchy` is a ranked list, **highest authority first** (rank 0 wins). For each
field the engine gathers candidate observations, **drops any from a source not in the
hierarchy** (queued as `unpermitted_source`), then:

- **all approved candidates agree** (strings equal after normalization; numbers within
  `numeric_tolerance`) → **agreed**; the proposed value is the highest-ranked source's value;
  confidence `agreed` (≥2 sources) or `single_source` (exactly one).
- **approved candidates disagree** → **conflicted**; the proposed value is the **top-ranked
  source's** value, flagged `requires_steward_review`, confidence `conflict`, and an
  `attribute_conflict` is queued. Selecting the top-ranked value is a *draft* pending review,
  never an adjudication of which source is correct.
- **no approved candidate** → **missing** if the field is in `required_fields` (queues
  `missing_required`), otherwise **absent** (no proposal, no conflict).

**Freshness:** the selected candidate's `as_of` is compared to `as_of − freshness_days`. If it
is older, the proposal is still emitted but flagged stale (`requires_steward_review`) and a
`stale_value` conflict is queued. A value can be *agreed but stale*.

## Identifier handling (identity is a hard boundary)

Identifiers are grouped by `scheme` within a `security_key`:

- **one distinct approved value** that passes its structural/check-digit test → **agreed_id**;
  an identifier proposal is emitted.
- **two or more distinct values for the same scheme** → **identifier_conflict** (an identity
  conflict). **No proposal is emitted**; the conflict is queued with `requires_steward_review`.
- **structurally invalid** value (fails the bundled check) → **identifier_invalid**. **No
  proposal is emitted**; queued for steward review.

`ISIN` (12 chars: 2-letter country + 9 alphanumeric + 1 Luhn check digit) and `CUSIP` (8 base
chars + 1 mod-10 check digit) are validated deterministically offline; schemes without a
bundled check are treated as structurally acceptable. **This skill never chooses between
conflicting identities and never merges records** — that is a steward decision.

## Conflict taxonomy

| Conflict type | Fires when | Proposal emitted? | Severity |
| ------------- | ---------- | ----------------- | -------- |
| `identifier_conflict` | Same `security_key`+scheme, ≥2 distinct identifier values | **No** — identity, steward only | identity |
| `identifier_invalid` | Identifier fails its check-digit / structural test | **No** — identity, steward only | identity |
| `attribute_conflict` | Approved sources disagree on a non-identity field | Yes (top-ranked, flagged) | material / minor |
| `stale_value` | Selected value's `as_of` older than the freshness window | Yes (flagged) | material / minor |
| `missing_required` | A `required_fields` field has no approved value | No | material |
| `unpermitted_source` | A candidate comes from a source not in the hierarchy | No (candidate excluded) | minor |

`material` vs `minor` is set by whether the field is in `material_fields`. Identity conflicts
are always severity `identity` and always require steward review.

## Tie-out invariants (enforced by `scripts/validate_output.py`)

1. **Field accounting:** every field maps to exactly one disposition; `agreed + conflicted +
   missing + absent == securities × 8` (`residual == 0`). A field left unaccounted for fails
   closed.
2. **Proposal accounting:** attribute proposals `== agreed + conflicted`. Identifier proposals
   are emitted only for `agreed_id` schemes.
3. **Conflict-queue accounting:** `len(conflict_queue) == Σ counts by conflict type`, and the
   reported `summary.by_conflict_type` matches the queue.
4. **Provenance:** every proposal cites ≥1 approved source.
5. **Identity boundary:** no proposal exists for a scheme with an `identifier_conflict` /
   `identifier_invalid`; those conflicts carry no `proposed_value` and require steward review.

## Idempotency & lineage

`input_fingerprint` = SHA-256 of the normalized inputs + config. `enrichment_id` =
`sme-{entity}-{as_of}-{fingerprint[:8]}`. It has **no timestamp or random component**, so
identical inputs reproduce an identical enrichment pack. Every proposal traces to its source
observations via `provenance` citations of the form `{source}:{field-or-scheme}@{as_of}`.

## Hard boundaries (fail closed)

- **Propose, never post.** Every proposal is `status: "PROPOSED"`. The skill never creates a
  security, never writes to the security master, and never promotes a record to golden/
  production.
- **Never resolve or merge identities.** Conflicting or invalid identifiers are queued for a
  security steward; the skill emits no identity proposal for them.
- **Do not decide which source is right.** Selecting the top-ranked value on an
  `attribute_conflict` is a draft pending steward review, not an adjudication.
- **No investment advice.** The skill enriches reference/static data; it never recommends
  buying, selling, or weighting a security or issuer.
- **Config is a versioned contract.** Required/material fields, tolerance, freshness window,
  and source ranking come from `config`, never tuned per-job to make a conflict disappear.
