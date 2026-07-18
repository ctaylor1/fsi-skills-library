# Changelog — transaction-process-tracker

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to keep an M&A
/ capital-markets deal process organized as a draft, source-linked tracker — separate from
the human decisions (bid selection, exclusivity, go/no-go) and operational actions (sending
outreach, executing NDAs, granting data-room access, delivering materials) it only records.

- **Scope:** per-party stage / NDA / data-room-access / bid status with citations;
  deterministic process-control gates; overdue and due-soon reminders; auditable change log
  vs. a prior snapshot; recorded and outstanding approvals; open-items list. Draft-only
  (`tracker_status` draft-tracker); no system-of-record change.
- **Controls:** R2, external-delivery approval. No bid selection / counterparty
  recommendation / exclusivity; no send / grant / execute / deliver; no fabricated or
  advanced status; no investment advice. Control gates (`nda-not-executed`,
  `access-not-granted`) surface exceptions and never auto-resolve. MNPI / client-confidential
  handling; versioned `config_version` and prior-snapshot dating.
- **Scripts:** `validate_input` (intake schema, milestone-citation and control-gate
  warnings), tracker engine (`calculate_or_transform`: stages, gates, reminders, change log,
  approvals, open items, source index), `validate_output` (required sections, no unsupported
  claims, control-gate consistency, required-approvals capture, decision/execution language
  screen, draft-status and standing-note checks). Each `--selftest` reads a bundled fixture.
- **Assets:** `output-template.md` rendering the canonical tracker sections (versioned
  contract with `validate_output`).
- **Evaluations:** trigger/routing, golden Project Atlas process (5 parties exercising a
  control exception, overdue/due-soon reminders, change log, and an outstanding approval),
  deterministic script checks, a non-compliant-output safety check (`expect_exit 1`), and
  injection / recommendation / delivery-authorization refusals.
- **Handoffs:** upstream `buyer-investor-list-builder`, `investment-banking-pitch-builder`;
  downstream `due-diligence-packager`, `lbo-model-builder`, `merger-model-builder`,
  `dcf-modeler`; human/operational handoffs for decisions, access, and delivery.

### Pending before release
- Deal-team / process-owner and compliance (MNPI, ethical-wall) blind review; template
  fidelity sign-off with a banking SME.
- Confirm the deal-process config source (stage order, required approvals, reminder window),
  owner, and versioning.
- Wire read-only MCP integrations (process CRM, DMS/NDA, VDR, governance/approvals) at
  deployment.
