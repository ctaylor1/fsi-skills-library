---
name: desk-pnl-risk-attribution-pack
description: >-
  Reconcile a trading desk's reported P&L to its risk-based attribution components (market P&L,
  carry, fees, new trades, funding) and deterministically compute the unexplained residual,
  flagging it as a break when it exceeds the configured tolerance, as a cited evidence packet for
  a product-control analyst. Use when an analyst asks to "attribute the desk P&L", "reconcile P&L
  to risk", "explain today's P&L", or "flag the unexplained residual". HARD BOUNDARY: R3
  decision-support only — it NEVER adjusts, restates, or books P&L, never signs off/attests/
  certifies the P&L, and never approves a break; every disposition is a recommendation an
  authorized human (product control) must adjudicate. Routes trade/position breaks to
  trade-break-resolver.
license: MIT
compatibility: Amazon Quick Desktop; requires desk P&L and risk-attribution feeds plus reference-data MCP integrations (all read-only). Deterministic stdlib-only computation.
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Product-control analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Desk P&L Risk Attribution Pack

## Purpose and outcome
Given a desk's reported P&L and its risk-based attribution components, deterministically compute
the explained total and the unexplained residual, flag the residual as a break when it exceeds
tolerance, and present the component contributions with cited evidence and a suggested review
disposition. A successful output lets a product-control analyst review — any P&L adjustment or
sign-off remains the authorized human's.

## Use when
- "Attribute the desk P&L", "reconcile P&L to risk", "explain today's P&L".
- "Flag the unexplained residual", "is the P&L within the attribution tolerance".
- A reviewer needs a consistent, cited P&L-attribution packet.

## Do not use
- The user wants you to **adjust, restate, book, or sign off** P&L → out of scope; product
  control acts.
- There is a **trade/position break** (fills/positions don't reconcile) → route to
  `trade-break-resolver`.
- Best-execution/venue review → `best-execution-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits an attribution packet with a durable
`attribution_id`; it does not adjust or sign off P&L.

## Inputs and prerequisites
- The **desk** context, the **reported_pnl**, the **components** (name, value, source_ref), and
  the **tolerance**. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Attribution taxonomy + tolerance are a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The P&L system is the reported figure;
risk feeds provide the components. Cite the residual and each component to its source.

## Workflow
1. **Validate input** — run `validate_input`; confirm reported_pnl and numeric components.
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): explained = Σ
   components; residual = reported − explained; flag if |residual| > tolerance; rank component
   contributions.
3. **Assemble the packet** — explained, residual, unexplained flag, contributions, citations.
4. **Suggest disposition** — `tied` or `breaks-for-review` (a triage suggestion, not a sign-off).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for the
   explained + residual == reported identity, the no-adjust/no-signoff screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If explained + residual ≠ reported, or the text
contains adjustment/sign-off language, **fix or fail closed**.

## Human approval
`required`: no P&L adjustment, restatement, booking, or sign-off/attestation without an
authorized human (product control). The skill only evidences the attribution.

## Failure handling
- **Non-numeric component** → exclude and flag; never coerce; the residual is then incomplete.
- **Missing tolerance** → fail closed; do not invent a threshold.
- **Residual within tolerance** → still report it; small ≠ zero; do not suppress.
- **Stale/conflicting feed** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — desk (masked), as_of, reported P&L, explained, residual, within-tolerance flag.
2. **Contributions** — components ranked by absolute contribution, each cited.
3. **Break** — residual and whether it exceeds tolerance.
4. **Machine-readable** — attribution + `attribution_id`.
5. **Standing disclaimer** — "Attribution evidence only; not a P&L adjustment, restatement, or
   sign-off. No P&L has been adjusted or certified."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask desk/book identifiers as needed. Retain attribution + citations +
tolerance version. Log read + external-delivery approval. Never exfiltrate P&L data.

## Gotchas
- **A residual is not an error to fix.** Flag it; product control investigates and adjusts.
- **Sign convention**: fees/funding are typically negative contributions; carry them with sign,
  never absolute.
- **Within tolerance ≠ explained** — a small residual is still unexplained P&L; report it.
- **Never certify or sign off the P&L** — evidence only.
