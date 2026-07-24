---
name: trade-idea-evidence-packet
description: >-
  Assemble a supporting-evidence packet for a trade idea — thesis, cited supporting data points,
  risk factors, and surfaced suitability/eligibility flags — and deterministically check that every
  data point is cited and every required section is present, as a review packet for a sales/trading
  analyst. Use when an analyst asks to "build the trade-idea evidence packet", "back up this trade
  thesis with cited data", "package the supporting evidence for this idea", or "what are the risks
  and citations for this idea". HARD BOUNDARY: R3 draft/decision-support only — it packages
  evidence for internal review; it NEVER recommends the idea to any specific client, makes a
  suitability/eligibility determination, or gives investment advice; a human and compliance own
  distribution and suitability. Routes client-specific RFQ prep to client-rfq-preparation-brief.
license: MIT
compatibility: Amazon Quick Desktop; requires market-data, research, and suitability-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Sales/trading analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Trade Idea Evidence Packet

## Purpose and outcome
Given a trade idea, deterministically assemble a supporting-evidence packet — thesis, cited
supporting data points, risk factors, and surfaced suitability/eligibility flags — and check that
every data point is cited and every required section is present. A successful output is an
internal-review packet; distribution to any client and every suitability determination remain the
human's and compliance's.

## Use when
- "Build the trade-idea evidence packet", "back up this trade thesis with cited data".
- "Package the supporting evidence for this idea", "what are the risks and citations".
- A reviewer needs a consistent, cited, risk-balanced idea packet.

## Do not use
- The user wants to **recommend the idea to a specific client** or a **suitability determination**
  → out of scope; the human/compliance decides.
- The user wants a **client-specific RFQ brief** → route to `client-rfq-preparation-brief`.
- The user wants **pricing/hedging scenarios** → `pricing-hedging-scenario-calculator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a packet with a durable `packet_id`;
it does not recommend to a client or decide suitability.

## Inputs and prerequisites
- The **idea** (instrument, direction, thesis), **data_points** (claim, value, source_ref),
  **risk_factors**, **suitability_context** (restricted_products, general_only), and a
  **checklist**. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Every claim must be cited; risk factors must be present. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Market data and research are the
evidence; cite every data point.

## Workflow
1. **Validate input** — run `validate_input`; confirm the idea, data points, and checklist.
2. **Assemble (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): build the sections,
   flag uncited data points, surface suitability/eligibility flags, and check required-section
   completeness.
3. **Assemble gaps/flags** — per gap/flag: reason, evidence, citation.
4. **Suggest disposition** — `packet-ready` or `gaps-for-review` (a triage suggestion, not a
   recommendation).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-client-recommendation/no-suitability screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a data point is uncited, or the text contains
client-recommendation/suitability language, **fix or fail closed**.

## Human approval
`required`: no recommendation to a specific client, suitability/eligibility determination, or
investment advice without the human/compliance. The skill only packages internal evidence.

## Failure handling
- **Uncited data point** → flag; never present an uncited claim as evidence.
- **No risk factors** → flag as a balance gap; an idea packet must carry its risks.
- **Restricted product** → surface a flag; never clear it.
- **Missing required section** → completeness gap; do not fabricate content.

## Output contract
1. **Summary** — idea id, instrument, direction, disposition, gap/flag counts.
2. **Sections** — thesis, cited evidence (data points), risk factors, suitability flags.
3. **Gaps & flags** — uncited data points, missing sections, restricted/general-only flags, each cited.
4. **Machine-readable** — sections + gaps + flags + `packet_id`.
5. **Standing disclaimer** — "Trade-idea evidence packet for internal review only; not a
   recommendation to any specific client, a suitability/eligibility determination, or investment
   advice."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII (if any client context is referenced). Keep the packet idea-level and internal.
Retain packet + citations. Log read + external-delivery approval. Never exfiltrate across the wall.

## Gotchas
- **Evidence is not a recommendation.** The packet backs a thesis for internal review; it never
  tells a client to trade.
- **Risks are mandatory** — an idea packet without risk factors is unbalanced; flag it.
- **Uncited claims are not evidence** — flag them; never present them as support.
- **Suitability is compliance's call** — surface flags, never determine suitability.
