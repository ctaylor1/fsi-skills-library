---
name: security-master-enricher
description: >-
  Join approved identifier, issuer, currency, exchange, asset-class, maturity, coupon, rating,
  and benchmark observations across ranked approved sources: apply a source hierarchy to draft
  one PROPOSED enriched value per field with provenance, classify
  every disagreement or data-quality issue into a fixed conflict taxonomy (identifier_conflict,
  identifier_invalid, attribute_conflict, stale_value, missing_required, unpermitted_source), and
  emit a steward conflict queue that ties out. Use when a security-master analyst asks to "enrich
  the security master", "join vendor identifiers and classifications", "reconcile reference-data
  attributes across sources", or "build the conflict queue for steward review" for instrument
  static data. HARD BOUNDARY: this skill PROPOSES enrichment only — it never creates a production
  security, and never resolves or merges conflicting identities or writes to the security master;
  every proposal and identity conflict requires security-steward review and authorized posting.
license: MIT
compatibility: Amazon Quick Desktop; requires reference-data-vendor, issuer/exchange-filing, entity-resolution, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Security-master analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Security Master Enricher

## Purpose and outcome
Given candidate securities with identifier and attribute observations from one or more
**approved** reference-data sources, deterministically **join** those observations, apply a
ranked **source hierarchy** to draft one **PROPOSED** enriched value per field with **provenance**,
**classify** every disagreement or data-quality issue into a fixed **conflict taxonomy**, and
emit a **steward conflict queue** that **ties out**. A successful output lets a security-master
analyst hand a reviewer a set of well-evidenced enrichment proposals to approve and post, plus a
prioritized queue of conflicts — above all the **identity** conflicts a steward must resolve. The
skill never creates the security and never resolves the identity itself.

## Use when
- "Enrich the security master for these instruments from the vendor feeds."
- "Join the vendor identifiers, issuer, currency, asset class, and ratings and show the conflicts."
- "Reconcile the reference-data attributes across vendor-a / vendor-b / internal and propose values."
- "Build the steward conflict queue for the securities that don't agree."

## Do not use
- You want a security **created** or an identifier **conflict resolved / merged** → out of scope.
  Propose and queue only; an authorized security steward decides identity and posts (see
  [references/handoffs.md](references/handoffs.md)).
- The task is comparing **internal book values vs an external vendor** field-by-field with as-of
  discrepancies → `investment-vendor-feed-reconciler`.
- The task is **monitoring feed data quality** (stale prices, implausible moves, broken mappings)
  into a prioritized exception queue → `investment-data-quality-exception-detector`.
- The conflict is a **price / valuation** exception (stale, disputed, outlier price) →
  `valuation-exception-packet`.
- You need to **normalize positions / cash / transactions** into the canonical schema →
  `holdings-transaction-normalizer`.
- You want a **buy/sell/weighting** view on a security or issuer → out of scope; this skill
  enriches reference data and gives no investment advice.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an enrichment pack with a
durable `enrichment_id`, PROPOSED values with provenance, and a classified conflict queue, then
stops. `investment-source-ingester` and `holdings-transaction-normalizer` may feed it approved
source observations; downstream skills consume its `enrichment_id` rather than re-joining. It
never creates a security, never resolves an identity, and never approves its own proposals.

## Inputs and prerequisites
- `entity`, `as_of` (run date), `config_version`, `source_hierarchy` (ranked, highest first).
- **securities[]**, each with `security_key` (an internal candidate key, **not** a confirmed
  identity), `identifiers[{scheme, value, source, as_of}]`, and
  `attributes[{field, value, source, as_of, effective_date?}]`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the reference-data sources; approved enrichment `config` (required/material
  fields, tolerance, freshness window) — see
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Vendors and internal overrides are
**independent observations of the same datum**, ordered by the versioned `source_hierarchy`. An
observation from a source not in the hierarchy is excluded (`unpermitted_source`). A conflict is
a disagreement between sources; the skill drafts the top-ranked value for review and evidences
the conflict — it does not decide which source is canonical, and it never resolves an identity.

## Workflow
1. **Scope & validate** — confirm `entity`/`as_of`/`source_hierarchy`; load candidate
   observations; run [scripts/validate_input.py](scripts/validate_input.py). Fail closed on
   structural gaps.
2. **Join & classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to group observations
   by `security_key`, select the top-ranked approved value per field, validate identifiers
   (ISIN/CUSIP check digits), and classify each disagreement or data-quality issue into the
   taxonomy (`identifier_conflict`, `identifier_invalid`, `attribute_conflict`, `stale_value`,
   `missing_required`, `unpermitted_source`). Each proposal carries provenance and a
   `requires_steward_review` flag; identity conflicts carry **no** proposed value.
3. **Tie out** — confirm every field maps to exactly one disposition and the conflict queue
   accounts for every classified issue (`residual == 0`). If it does not tie, surface it; never
   drop a field or a conflict.
4. **Draft proposals (PROPOSED only)** — for each agreed or conflicted field, emit a
   `status: "PROPOSED"` value with its selected source and provenance. Missing/identity/unpermitted
   items produce **no** proposal — only a queue entry.
5. **Write the pack** — plain-language summary + tie-out + proposals with provenance + the steward
   conflict queue + the standing no-creation/no-resolution disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms tie-outs (field dispositions account for every field; proposals ==
agreed + conflicted; queue length == Σ counts by type), the conflict taxonomy, provenance on
every proposal, the identity boundary (no proposal for a conflicting/invalid identifier),
proposed-only status with no creation/resolution or investment-advice language, idempotency of the
`enrichment_id`, and the disclaimer. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the enrichment pack or any proposal is
delivered externally or written to a system of record. **Creating the security, resolving the
identity, or writing the master is always a separate, authorized security-steward action**
performed under segregation of duties — never by this skill.

## Failure handling
- **Doesn't tie out** (a field unaccounted for, queue count mismatch) → report it; do not drop a
  field or silently reconcile.
- **Conflicting identifiers** → queue `identifier_conflict`; never pick one or merge — route to a
  steward.
- **Invalid identifier** (check-digit failure) → queue `identifier_invalid`; emit no identifier
  proposal.
- **Unpermitted source** → exclude the observation and queue `unpermitted_source`; never fall back
  to an unapproved value.
- **Missing required field** → queue `missing_required`; do not infer or fabricate a value.
- **Stale value** → still propose the top-ranked value but flag `stale_value` for steward review.
- **Tool timeout** → return the proposals/conflicts computed so far with a clear "incomplete"
  flag; no assumed retry.

## Output contract
1. **Summary** — entity, `as_of`, securities, proposal count, conflict count, counts by conflict
   type, steward-review count, `enrichment_id`.
2. **Tie-out** — `fields_considered`, `dispositions` (agreed/conflicted/missing/absent),
   `residual` (must be 0), `attribute_proposals`, `identifier_proposals`, `conflicts_total`,
   `reconciled`.
3. **Enrichment proposals** — per proposal: `field`/`scheme`, `proposed_value`, `selected_source`,
   `confidence`, `provenance`, `requires_steward_review`, `status: "PROPOSED"`, `conflict_id` (if
   any). Identifier proposals only for agreed, valid schemes.
4. **Conflict queue** — per conflict: `type`, `field`, `severity`, `candidates`, and
   `requires_steward_review`; identity conflicts carry no proposed value.
5. **Machine-readable** — the full enrichment JSON + `enrichment_id` + `input_fingerprint` for
   downstream skills and reproducibility.
6. **Standing disclaimer** — "Enrichment proposals and conflict queue only; no security has been
   created, no identity has been resolved or merged, and nothing has been written to the security
   master. All proposals and identity conflicts require security-steward review and authorized
   posting."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Reference-data enrichment needs no customer NPI;
operate on instrument static data, not client positions, and minimize any holdings detail. Retain
the pack, proposals, provenance, conflict queue, and `config_version` per records policy; log the
read and any external-delivery approval.

## Gotchas
- **Propose, never create.** A proposal is a draft; the skill has no create/write operation. The
  disclaimer and `status: "PROPOSED"` are load-bearing controls, not decoration.
- **Identity is a hard boundary.** Two different ISINs for one `security_key`, or a failed check
  digit, are **never** resolved here — they are steward decisions. The engine emits no identity
  proposal for them.
- **Top-ranked is a draft, not a verdict.** Selecting the highest-ranked source on an
  `attribute_conflict` is pending steward review; the skill does not declare a source correct.
- **Config is a versioned contract.** Required/material fields, tolerance, freshness window, and
  source ranking come from `config`, never tuned per-job to make a conflict disappear.
- **Agreed can still be stale.** A value all sources agree on is still flagged if it is older than
  the freshness window — agreement is not freshness.
- **Unpermitted sources are excluded, not ranked last.** An observation from an unapproved source
  is dropped and queued, never used as a fallback value.
- **No investment advice.** Enriching a rating or benchmark is reference data, never a view on the
  security or issuer.
