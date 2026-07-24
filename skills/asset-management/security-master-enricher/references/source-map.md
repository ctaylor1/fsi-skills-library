# Source Map — security-master-enricher

## Source hierarchy (highest first)

The `source_hierarchy` is a **versioned, ranked contract** supplied per job; the ranks below
are the typical deployment ordering. Rank 0 wins ties; any observation from a source **not**
in the hierarchy is excluded and queued as `unpermitted_source`.

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 0 | **Primary reference-data vendor** (e.g. `vendor-a`) | Identifiers, classifications, terms, ratings | Read-only |
| 1 | **Secondary reference-data vendor** (e.g. `vendor-b`) | Cross-check / fallback observations | Read-only |
| 2 | **Internal analyst / golden overrides** (`internal`) | Curated internal reference values | Read-only |
| 3 | **Issuer / exchange filings** | Issuer relationships, listing, maturity/coupon terms | Read-only |
| 4 | Enrichment **config** (versioned) | Required/material fields, tolerance, freshness window, source ranking | Read-only |

The vendors and internal overrides are **independent observations of the same reference
datum**; none is subordinate outside the declared ranking. A conflict is a disagreement
between them — the skill classifies and evidences it and drafts the top-ranked value for
review; it does **not** decide which observation is canonical, and it **never** resolves a
conflicting *identity*.

## Input schema (validated by `scripts/validate_input.py`)

Top level: `entity`, `as_of` (YYYY-MM-DD), `config_version`, `source_hierarchy[]`,
`securities[]`, `config{}`.

Each security:
`security_key` (internal candidate key — **not** a confirmed identity),
`identifiers[{scheme, value, source, as_of}]`,
`attributes[{field, value, source, as_of, effective_date?}]`.

`config`: `required_fields[]`, `material_fields[]`, `numeric_tolerance`, `freshness_days`.

## Citation format

`{source}:{field-or-scheme}@{as_of}` — e.g. `vendor-a:asset_class@2026-06-28` and
`vendor-b:ISIN@2026-06-27`. Every proposal carries a `provenance` list of the source
observations it was joined from; every conflict lists its candidate observations.

## Freshness / effective dates

- `config` (required/material fields, tolerance, freshness window, source ranking) is a
  **versioned contract**; the output records `config_version` so a run is reproducible.
- `as_of` fixes the run date. A selected value whose `as_of` predates `as_of − freshness_days`
  is proposed **and** flagged `stale_value` for steward review.
- `effective_date` on an attribute records when the term became effective (e.g. a maturity or
  coupon schedule) and is carried onto the proposal for the steward.
- `input_fingerprint` (a content hash of the normalized inputs + config) makes the
  `enrichment_id` a pure function of the inputs — re-running the same inputs is idempotent.

## Least-privilege operations (deployment)

- `refdata.read(entity, security_key[], as_of)` → bounded, paged candidate observations per
  source.
- `hierarchy.get('security-master', version)` → the ranked source hierarchy + config.
- `enrichment.get(enrichment_id)` → a prior pack for carry-forward of open conflicts.

All read-only, deterministic, durable `enrichment_id`, below the fixed timeout; page long
universes as resumable stages. **No create/merge/write operation is bound to this skill** —
proposals and identity conflicts are handed to an authorized security steward to post. The
platform services (entity resolution, deterministic computation, controlled content library,
data governance) are referenced, not reimplemented — see the library `docs/SHARED-SERVICES.md`.
