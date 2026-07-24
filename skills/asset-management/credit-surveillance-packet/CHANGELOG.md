# Changelog — credit-surveillance-packet

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
- **Handoffs:** upstream `investment-source-ingester`, `holdings-transaction-normalizer`,
  `security-master-enricher`, `investment-vendor-feed-reconciler`; downstream/adjacent
  `credit-terms-covenant-extractor` (mandated covenant handoff), `investment-thesis-monitor`,
  `counterparty-exposure-monitor`, `fund-commentary-drafter`; human handoffs for rating, thesis,
  position, and covenant-compliance determination.

### Pending before release
- Credit-research control-owner + compliance (MNPI / wall-crossing) blind review.
- Confirm the metric/threshold config and packet-template source, owner, and versioning; confirm
  the fixed-charge coverage definition for the deployment (scheduled principal inclusion).
- Wire read-only MCP integrations (filings, credit agreement, rating-agency, market data,
  spreading service, reference data) at deployment.
