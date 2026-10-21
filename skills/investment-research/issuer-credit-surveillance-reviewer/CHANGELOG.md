# Changelog — issuer-credit-surveillance-reviewer

## [0.4.1] — 2026-10-20

- Retire the legacy public request/output runtime, which lacked the current reported-period and quote-evidence controls. All live input, calculation and output entrypoints require explicit `ir-phase2/1.0` original requests and return a controlled migration-required error for legacy contracts. No automatic conversion or compatibility bypass is provided.
- Use the supported analytical contract for advertised schema, rendering, selftests and positive evals. Retain legacy fixtures as rejection evidence and preserve earlier phase/repair artifacts with their frozen source.
- Add public-command and direct-API migration regressions for future reported financials, stale/undated/unmapped quotes, wrong schema labels, current supported/partial results and whole-output mutation rejection.

## [0.4.0] — 2026-10-20

- Reconcile analytical spread assertions against selected structured market observations, registered source versions/precise blocks and a dated security/issuer/currency mapping. Bind issuer or exact security scope to the request and calculate spread changes from reconciled observations.
- Withhold the comparison and widening alert for missing, duplicate, conflicting, unrelated or wrong-role evidence; retain supported financial metrics and the existing whole-projection source gate. Return selected evidence context only for reconciled comparisons.
- Add independent numerical, source-role, mapping-validity, claim/evidence disagreement and public-command regressions, plus active adverse fixtures. Preserve prior phase/repair evidence and the legacy Phase 1 contract. Supplied evidence remains unauthenticated.

## [0.3.1] — 2026-10-20

- Reject Phase 2 reported financial periods ending after economic as-of.
- Require explicit quote observations and current-age policy for spread changes, with precise ordering, economic as-of, source-knowledge and cutoff checks. Missing/stale/incomparable evidence withholds the change and widening alert while retaining supported financial metrics.
- Add boundary, source-vintage and public-command regression coverage. Earlier phase records and the legacy Phase 1 contract remain preserved.

## [0.2.0] — 2026-10-20

- Repair Phase 1 input/domain/source-vintage and faithful-partial controls; require whole-output reconstruction from separately retained originals.
- Preserve load-bearing identity, source/basis and review limits; source/role assertions remain unverified and cannot grant action authority.
- Update native schema, supplied-input documentation, positive fixtures and executable eval commands; add independent expected arithmetic, mutation and invalid-shape regressions.
- Bounded software evidence only; no new Phase 2 research engine, live action or institutional/practitioner acceptance.

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — issuer-credit-surveillance-reviewer

## Unreleased — Phase 1 source fidelity

- Near-term coverage uses exact maturity_date values over the inclusive as-of through calendar-year anniversary horizon. Past-due maturities are separate. Year-only dates produce an explicit coverage gap. Prior financials are included in source-reference checks. Leverage and fixed-charge coverage remain bounded corporate-financial calculations; the latter is a proxy.
- Added detached original-input reconstruction and independent adverse-case regressions. Validation remains draft-only and does not authenticate sources or approvals.


## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to give a credit
research analyst a controlled, fully-cited surveillance packet for a single issuer, with the
credit metrics computed and tied out deterministically and clear boundaries around rating,
thesis, position, and covenant work.

- **Scope:** compute and tie out leverage (gross/net), coverage (interest, fixed-charge proxy),
  and liquidity; lay out the maturity wall and near-term coverage; track current-vs-prior spread
  and reported agency ratings; flag covenant changes. Draft-only; no system-of-record change.
- **Controls:** R2; **reports** agency ratings but assigns none (`rating_action: reported-only`);
  never forms/alters a thesis (`thesis_action: unchanged`); never recommends/changes a position
  or trade (`position_action: none`); flags covenant changes but does not extract terms or
  determine compliance; no unsupported/unapproved claims; tie-out and prohibited-language screens;
  versioned template/metric config.
- **Scripts:** `validate_input` (request schema, needs-data warnings, approval + approved-source
  checks), `calculate_or_transform` (deterministic metrics + tie-outs + change tracking +
  covenant-change flags + section assembly, self-check ending "N error(s)"), `validate_output`
  (template fidelity, unsupported/unapproved claims, tie-outs, neutral action fields, recorded
  approvals, rating/thesis/position/covenant/advice/delivery language screen, standing note).
- **Evaluations:** trigger/routing (incl. rating/position/covenant-detail negatives), a golden
  issuer packet exercising every section and disclosure flag, deterministic script checks, a
  non-compliant packet safety check that fails closed (`expect_exit 1`), prompt-injection and
  covenant-compliance refusals, and a no-rating authorization check.
- **Handoffs:** upstream `research-source-indexer`, `investment-record-normalizer`,
  `investment-reference-data-reviewer`, `investment-data-quality-reviewer`; downstream/adjacent
  `credit-document-terms-reviewer` (mandated covenant handoff), `investment-thesis-monitor`,
  `counterparty-exposure-monitor`, `investment-commentary-builder`; human handoffs for rating, thesis,
  position, and covenant-compliance determination.

### Pending before release
- Credit-research control-owner + compliance (MNPI / wall-crossing) blind review.
- Confirm the metric/threshold config and packet-template source, owner, and versioning; confirm
  the fixed-charge coverage definition for the deployment (scheduled principal inclusion).
- Wire read-only MCP integrations (filings, credit agreement, rating-agency, market data,
  spreading service, reference data) at deployment.

## 0.3.0 — 2026-10-20

Added explicit Phase 2 supplied-evidence analytical mode while preserving the prior native contract and its regression evidence.
