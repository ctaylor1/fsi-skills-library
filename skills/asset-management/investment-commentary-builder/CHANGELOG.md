# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — investment-commentary-builder

## Unreleased — Phase 1 source fidelity

- Numeric inputs must be finite and parseable; malformed values never become zero. Unreconciled performance and attribution are withheld from the claim ledger. Contribution labels preserve their sign. Free-text claims require exact matching current approved-message text; an existing citation ID alone cannot substantiate them. as_of_date governs message availability independently of the performance period. Output remains an unapproved draft.
- Added detached original-input reconstruction and independent adverse-case regressions. Validation remains draft-only and does not authenticate sources or approvals.


## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). A Draft & package
(R2) skill that assembles periodic fund commentary from reconciled sources with claim-level
substantiation, tie-out evidence, and mandatory product + compliance sign-off.

- **Scope:** draft monthly/quarterly fund commentary from reconciled performance and
  attribution, positioning, flows, market context, and the approved messaging library;
  build a claim ledger where every statement is source-cited; flag and exclude unsupported
  claims. Draft-only; never sends, files, publishes, or distributes.
- **Controls:** R2 / `external-delivery`; performance excess and attribution tie-outs;
  claim substantiation and source/period fidelity; prohibited/misleading-language screen
  (guarantees, "will outperform", "risk-free", ...) over narrative only (disclosures
  excluded); required-disclosure check; product **and** compliance approvals recorded before
  delivery; `delivery_status` never set to sent/distributed.
- **Scripts:** `validate_input` (commentary-inputs schema + tie-out/data-quality warnings),
  `calculate_or_transform` (deterministic tie-outs + claim-ledger assembly + unsupported-claim
  flagging), `validate_output` (required sections, tie-outs, substantiation, language screen,
  disclosures, approvals, draft-only, standing note).
- **Assets:** `assets/output-template.md` — controlled commentary template with the seven
  required sections and the sign-off block.
- **Evaluations:** trigger/routing, golden commentary task (12 supported claims, both
  tie-outs), deterministic script checks, non-compliant-package safety check (unsupported
  claim + prohibited language + missing compliance approval → fail closed), guarantee/
  fabrication refusals, no-send and no-self-approve authorization checks.
- **Handoffs:** upstream `portfolio-performance-attributor`, `portfolio-exposure-analyzer`,
  `fund-liquidity-assessor`; downstream `communications-compliance-reviewer` and human
  product/compliance approvers; siblings `fund-fact-sheet-builder`,
  `investment-committee-memo-builder`, `institutional-proposal-responder`.

### Pending before release
- Product + compliance (marketing-review) blind sign-off of the template and the
  prohibited-language / disclosure screens; segregation-of-duty confirmation.
- Confirm the approved messaging library and disclosure set source, owners, and versioning
  per fund/jurisdiction; configure non-US jurisdiction packs.
- Wire read-only MCP integrations (performance, attribution, holdings, flows, market data,
  controlled content) at deployment.
