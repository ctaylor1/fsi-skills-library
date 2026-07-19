# Changelog — payment-exception-investigator

## [Unreleased]
- **Fix (priority tie-out):** `validate_output` no longer disagrees with the builder on
  `priority_band`. It now recomputes the expected band using the same fraud/sanctions risk override
  the builder applied (surfaced as the new `priority_risk_override` flag) — the `route-specialist`
  disposition alone no longer forces `P1` — and reads the P1/P2 thresholds from the effective
  priority config the builder echoes as `priority_thresholds`, instead of hardcoding 6/3. This
  removes false failures on reason-code route-specialist cases (RR04/FRAD without a fraud/sanctions
  flag) and on any non-default `priority_config`. Added `evals/files/exceptions_nondefault_config.json`
  (+ generated `investigation_nondefault_config.json`) as a `det-output-nondefault-config` eval that
  now validates clean, and `investigation_nondefault_config_tampered_band.json` as a
  `safety-priority-tamper-nondefault` eval proving the tie-out still fails closed when a
  sanctions-flagged case is buried below `P1`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
substantive **payment exception investigation** from upstream diagnosis/interpretation and from
downstream repair execution (distinct entitlements, evidence depth, and case states).

- **Scope:** emit a durable `case_id`; build a cited pacs/camt message chronology; trace status
  and ISO reason codes; resolve parties and amounts; compute a documented priority; and produce a
  **recommendation-only** disposition (repair / return / honor-recall / reject-recall /
  request-information) or a specialist route. Read-only; every next step is a proposal.
- **Controls:** R3; no fund movement, no case closure/determination/filing, no camt.029/pacs.004
  response sent; sanctions/regulatory and fraud signals force a specialist route; dedup links
  (never merges); needs-data on missing messages/identifiers; versioned ISO code-set and config.
- **Scripts:** `validate_input` (exception-batch schema, needs-data warnings), the investigation
  builder (chronology + last-status trace + documented priority + precedence + evidence bundle +
  recommendation), and `validate_output` (durable case_id, recommendation-only dispositions,
  full citation coverage, specialist-route check, priority tie-out, closure/fund-movement/filing
  language screen, standing note).
- **Evaluations:** trigger/routing, a golden 9-exception queue exercising every disposition,
  deterministic script checks, a fail-closed safety fixture (closure + fund-movement + filing
  language), fund-movement and prompt-injection refusals, and a closure-authorization refusal.
- **Handoffs:** upstream from `payment-failure-diagnoser` and `iso-20022-message-interpreter`;
  downstream to `payment-repair-assistant`, `sanctions-match-adjudicator`,
  `payment-fraud-case-investigator`, `dispute-operations-assistant`, `chargeback-dispute-packager`,
  `transaction-reconciliation-helper`, and `settlement-break-reconciler`.

### Pending before release
- Payments control-owner + operations blind review; segregation-of-duty review (investigate vs.
  repair execution).
- Confirm the ISO external code-set source/version, screening/repair-rule config owner, and
  scheme-rulebook recall/return windows.
- Wire read-only MCP integrations (case-management, message store, code sets, reference, rules) at
  deployment.
