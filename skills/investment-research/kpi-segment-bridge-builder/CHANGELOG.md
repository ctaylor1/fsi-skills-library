# Changelog - kpi-segment-bridge-builder

## 0.2.0 — 2026-10-20

- Require detached original input for native output validation; reconstruct every result and reject omissions, alterations and extra fields. Guard finite numbers, shapes, dates, domains and duplicates; validate before computation.
- Use only closed historical periods with permitted sourced inputs. Referenced authoritative totals must exist. Unrequested reconciliation is not evaluated and never counts as reconciled; the pack reports partial-or-not-evaluable coverage. Mapping IDs are unique, approved and effective on/before the prior-period end so both bridged periods are covered. Full supplied context, including totals/citations/mappings, affects hashes. The volume-price joint term is a two-factor interaction, not general product-mix attribution.
- Regenerate synthetic positive and adversarial fixtures. Passing checks is not source authentication, professional acceptance or independent institutional assurance.


## [0.1.0] - 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic, source-linked KPI/segment bridge builder - extract disclosed
  operational KPIs and construct revenue, margin, volume-price, and segment bridges between two
  reported periods, with source-to-calculation tie-outs and reconciliation to the disclosed
  totals, as a draft for review.
- **Hard boundaries:** never forecast (forward-looking source types fail closed on input and
  output); never normalize accounting judgment beyond approved, versioned mappings (unapproved
  `mapping_id` rejected). No recommendation / price target / advice.
- **Controls:** R2; assumptions carry provenance + citation; `config_version` and
  `mapping_version` recorded; MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic walk + volume/price
  decomposition with an explicit joint-mix convention), `validate_output` (formula tie-outs,
  reconciliation, source-type + mapping discipline, no-forecast/no-advice screen, disclaimer).
  Python stdlib-only, self-contained, each with `--selftest` over a bundled fixture.
- **Evaluations:** trigger/routing, golden four-bridge task, deterministic script checks,
  tie-out + boundary safety fixture (fails closed), injection, external-delivery authorization.
- **Handoffs:** upstream `financials-normalizer`, `financial-spreading-assistant`,
  `earnings-results-analyzer`, `company-profile-builder`; downstream `dcf-modeler`,
  `three-statement-model-builder`, `scenario-sensitivity-generator`, `valuation-reviewer`,
  `due-diligence-packager`, `investment-banking-pitch-builder`.

### Pending before release
- Domain SME (research) blind review; accounting-policy review of the approved mapping set.
- Wire read-only filings / disclosed-KPI / mapping-registry MCP integrations at deployment.

## 2026-09-20 — Category ownership migration

- Moved from Investment Banking & Research to Investment Research; stable skill ID retained.
- Native method and information/publication controls unchanged. Path alias is registered.

## 0.3.0 — 2026-10-20

Phase2 mode decomposes historical segment EBIT changes into prior-margin revenue effects and current-revenue margin effects, with unallocated change when zero denominators prevent decomposition. Explicit versioned reviewed-supplied mappings must cover both historical periods. Segment sums are independently reconciled to supplied reported totals. The result remains historical and does not forecast or authorize mappings.
