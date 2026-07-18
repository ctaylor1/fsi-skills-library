# Changelog — buyer-investor-list-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to build and
prioritize a buyer / investor / lender / sponsor universe for a defined mandate as a controlled,
source-mapped internal draft, separate from conflicts clearance, deal-process execution, and
client delivery.

- **Scope:** score candidates against documented fit criteria, attach cited rationale and
  relationship context, screen against the firm restricted / conflicts list, and tier placeable
  candidates into outreach waves. Draft-only; external delivery and buyer outreach are proposed,
  human-gated actions — never performed by the skill.
- **Controls:** R2; no send/deliver/share of the list; no buyer contact or outreach execution;
  restricted/conflicted candidates held as `hold-conflicts-review` and excluded from every wave;
  no unsupported assertions (every rationale claim cites an indexed source); no recommendation,
  valuation opinion, or investment advice; required approvals (`deal_lead`,
  `conflicts_reviewer`) gate external delivery; versioned restricted-list / fit-scoring config.
- **Scripts:** `validate_input` (intake schema; needs-data / needs-source / restricted /
  approval warnings), the deterministic list builder (`calculate_or_transform`: rationale
  citation binding, documented fit score, wave tiering, restricted/conflict hold, duplicate
  linking, gaps), and `validate_output` (required sections, no unsupported claims, fit→wave
  tie-out, restricted-never-in-wave, approvals gate, send/outreach + advice screens, standing
  note).
- **Assets:** `assets/output-template.md` with the 10 required section anchors checked by
  `validate_output`.
- **Evaluations:** trigger/routing (positive/negative, and handoffs to
  `conflicts-of-interest-reviewer`, `transaction-process-tracker`,
  `investment-banking-pitch-builder`), an 8-candidate golden universe exercising every
  disposition, deterministic script checks, a non-compliant-list safety check (fails closed),
  and no-delivery / no-advice / conflicts-override / prompt-injection / authorization safety
  cases.
- **Handoffs:** upstream from `company-profile-builder`, `market-landscape-researcher`,
  `comps-analysis-builder`, `due-diligence-packager`, `coverage-meeting-preparer`; downstream to
  `conflicts-of-interest-reviewer`, `transaction-process-tracker`,
  `investment-banking-pitch-builder`, and the human deal team for delivery/outreach.

### Pending before release
- Investment-banking control-owner + compliance (information-barrier / restricted-list) blind
  review; segregation-of-duty review (list building vs. conflicts clearance vs. delivery).
- Confirm the restricted/conflicts-list source, owner, and versioning, and the fit-scoring
  configuration owner.
- Wire read-only MCP integrations (market/financial data, filings, research, document
  intelligence, CRM, restricted-list) at deployment.
