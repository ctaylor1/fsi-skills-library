# Changelog — valuation-exception-packet

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
pricing-**exception investigation/packaging** from feed **reconciliation** (upstream) and from
the **price decision / NAV striking** (downstream, human), which carry distinct entitlements,
evidence depth, and outputs.

- **Scope:** on a fund book as of a valuation date, detect stale / missing / disputed / outlier
  prices, tag every candidate price as an observation or a hypothesis via the pricing hierarchy,
  score a documented severity band, and assemble a cited evidence bundle with a durable
  `case_id`. Read-only; recommendation-only disposition.
- **Controls:** R3; never selects/overrides a price, certifies/strikes NAV, or closes an
  exception; no hypothesis may be presented as an observed price; versioned tolerance/hierarchy
  config; MNPI / client-confidential and vendor-licensing handling.
- **Scripts:** `validate_input` (book/price schema, needs-data & missing warnings), the
  exception engine (`calculate_or_transform`: observation/hypothesis tagging, deterministic
  stale/missing/disputed/outlier detection, severity band, evidence bundle), and
  `validate_output` (durable IDs, allowed dispositions only, prohibited-field & decision-language
  screens, observation/hypothesis integrity, citation completeness, severity tie-out, standing
  note). Each script has a `--selftest` over a bundled fixture and prints a line ending in
  `N error(s)`.
- **Evaluations:** trigger/routing, golden 7-instrument book exercising every disposition and
  all four exception types, deterministic script checks, a no-decision safety check running
  `validate_output` on a non-compliant packet (fails closed), price-selection and NAV-certify
  refusals, and a disposition-authorization refusal.
- **Handoffs:** upstream from `investment-vendor-feed-reconciler`,
  `investment-data-quality-exception-detector`, and `nav-preparation-tie-out`; downstream to the
  human Valuation Committee (price decision) and fund accounting / NAV oversight (NAV striking).

### Pending before release
- Valuation control-owner + pricing-committee review; segregation-of-duty review (packaging vs.
  adjudication).
- Confirm the approved valuation-tolerance config and pricing-hierarchy source, owner, and
  versioning; confirm business-day/holiday calendar for staleness.
- Wire read-only MCP integrations (pricing/IBOR, approved vendors, broker quotes, trade blotter,
  corporate actions, tolerance config) at deployment.
