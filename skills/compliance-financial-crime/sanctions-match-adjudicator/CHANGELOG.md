# Changelog — sanctions-match-adjudicator

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created as the sanctions
casework counterpart to first-line AML triage: it adjudicates a screening HIT into a durable,
cited evidence bundle and a disposition RECOMMENDATION for an authorized sanctions officer,
keeping the block/reject/release and blocking/OFAC-report decision with the human.

- **Scope:** resolve the subject against the matched listed entity, compute documented match
  factors (corroborators/discriminators) across name/alias, identifiers, DOB, nationality, POB,
  address, ownership (OFAC 50% Rule), and transaction/jurisdiction nexus, build a chronology, and
  recommend a disposition. Read-only; a disposition is a *proposed* case-state transition via the
  approval broker.
- **Controls:** R3; no match confirmation/discount, payment block/reject/release, account
  block/unblock, case closure, or blocking/OFAC filing; documented screening provenance required
  (fail closed if absent); never clear on name alone (`needs-data`); conflict guard prevents
  auto-discounting conflicting strong signals; tipping-off / SAR-confidentiality screen; versioned
  match-factor / band config.
- **Scripts:** `validate_input` (screening-hit schema, provenance + name-only warnings), the
  adjudication engine (match factors + chronology + overrides + conflict guard + score bands +
  evidence bundle), `validate_output` (durable `SANC-<id>` case_id, provenance, allowed
  recommendations, evidence-citation completeness, `disposition_basis` tie-out, confirmation/
  block/release/filing language screen, standing note).
- **Evaluations:** trigger/routing, golden 7-hit set exercising every disposition and every
  basis (strong-id override, ownership 50%-Rule override, score-band discount, score-band L2
  review, needs-data, possible-duplicate, conflict-guard), deterministic script checks, a
  fail-closed safety fixture, and injection / name-only / tipping-off / decision-authorization
  refusals.
- **Handoffs:** upstream from the screening engine, `kyc-customer-due-diligence-screener`, and
  `aml-alert-triager`; lateral/downstream to `beneficial-ownership-verifier`,
  `enhanced-due-diligence-packager`, `adverse-media-investigator`, `customer-risk-rating-reviewer`,
  `transaction-monitoring-alert-investigator`, and (post-adjudication only)
  `suspicious-activity-report-drafter`; mandatory human adjudication by an authorized sanctions
  officer / OFAC compliance / MLRO.

### Pending before release
- Sanctions control-owner + legal (SAR-confidentiality / tipping-off) blind review; segregation-of-duty review.
- Confirm the match-factor weights, disposition bands, and ownership threshold against the firm's
  sanctions program standard, and their source, owner, and versioning.
- Wire read-only MCP integrations (sanctions/PEP list data, screening engine, KYC, transactions,
  case management) at deployment.
